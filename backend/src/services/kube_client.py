"""Thin async wrappers around the Kubernetes Python client.

Real GKE apply path; fully isolated from tests by the import-guard. The
orchestrator's fake provider path synthesises fake LB IPs without touching
this module — see ``deployment_orchestrator``.
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any

import yaml


async def apply_objects(kubeconfig_yaml: str, manifest_yaml: str) -> None:
    """Apply Secret + Deployment + Service using the official kubernetes client.

    The kubeconfig_yaml is written to a temp file because the client only loads
    from a file path.
    """
    loop = asyncio.get_event_loop()

    def _apply() -> None:
        from kubernetes import client, config

        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
            tmp.write(kubeconfig_yaml)
            kubeconfig_path = tmp.name

        try:
            config.load_kube_config(config_file=kubeconfig_path)
            core_v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()

            for doc in yaml.safe_load_all(manifest_yaml):
                if doc is None:
                    continue
                namespace = doc["metadata"].get("namespace", "default")
                kind = doc["kind"]

                if kind == "Secret":
                    _create_or_replace_secret(core_v1, namespace, doc)
                elif kind == "Deployment":
                    _create_or_replace_deployment(apps_v1, namespace, doc)
                elif kind == "Service":
                    _create_or_replace_service(core_v1, namespace, doc)
                else:
                    raise RuntimeError(f"Unsupported manifest kind: {kind}")
        finally:
            Path(kubeconfig_path).unlink(missing_ok=True)

    await loop.run_in_executor(None, _apply)


def _create_or_replace_secret(core_v1, namespace: str, doc: dict[str, Any]) -> None:
    from kubernetes.client.exceptions import ApiException

    name = doc["metadata"]["name"]
    try:
        core_v1.read_namespaced_secret(name=name, namespace=namespace)
        core_v1.replace_namespaced_secret(name=name, namespace=namespace, body=doc)
    except ApiException as exc:
        if exc.status == 404:
            core_v1.create_namespaced_secret(namespace=namespace, body=doc)
        else:
            raise


def _create_or_replace_deployment(apps_v1, namespace: str, doc: dict[str, Any]) -> None:
    from kubernetes.client.exceptions import ApiException

    name = doc["metadata"]["name"]
    try:
        apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        apps_v1.replace_namespaced_deployment(name=name, namespace=namespace, body=doc)
    except ApiException as exc:
        if exc.status == 404:
            apps_v1.create_namespaced_deployment(namespace=namespace, body=doc)
        else:
            raise


def _create_or_replace_service(core_v1, namespace: str, doc: dict[str, Any]) -> None:
    from kubernetes.client.exceptions import ApiException

    name = doc["metadata"]["name"]
    try:
        existing = core_v1.read_namespaced_service(name=name, namespace=namespace)
        # Services require clusterIP preservation on replace
        doc["spec"]["clusterIP"] = existing.spec.cluster_ip
        core_v1.replace_namespaced_service(name=name, namespace=namespace, body=doc)
    except ApiException as exc:
        if exc.status == 404:
            core_v1.create_namespaced_service(namespace=namespace, body=doc)
        else:
            raise


async def wait_deployment_available(
    kubeconfig_yaml: str,
    deployment_name: str,
    namespace: str = "default",
    timeout_seconds: int = 1800,
) -> None:
    loop = asyncio.get_event_loop()

    def _wait() -> None:
        from kubernetes import client, config

        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
            tmp.write(kubeconfig_yaml)
            kubeconfig_path = tmp.name

        try:
            config.load_kube_config(config_file=kubeconfig_path)
            apps_v1 = client.AppsV1Api()
            deadline = loop.time() + timeout_seconds
            while loop.time() < deadline:
                status = apps_v1.read_namespaced_deployment_status(
                    name=deployment_name, namespace=namespace
                ).status
                if status and status.available_replicas and status.available_replicas >= 1:
                    return
                import time
                time.sleep(5)
            raise TimeoutError(
                f"Deployment {deployment_name} did not become Available within {timeout_seconds}s."
            )
        finally:
            Path(kubeconfig_path).unlink(missing_ok=True)

    await loop.run_in_executor(None, _wait)


async def get_service_lb_ip(
    kubeconfig_yaml: str,
    service_name: str,
    namespace: str = "default",
    timeout_seconds: int = 900,
) -> str:
    loop = asyncio.get_event_loop()

    def _wait_for_ip() -> str:
        from kubernetes import client, config

        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
            tmp.write(kubeconfig_yaml)
            kubeconfig_path = tmp.name

        try:
            config.load_kube_config(config_file=kubeconfig_path)
            core_v1 = client.CoreV1Api()
            import time
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                svc = core_v1.read_namespaced_service(name=service_name, namespace=namespace)
                ingress = (
                    svc.status
                    and svc.status.load_balancer
                    and svc.status.load_balancer.ingress
                )
                if ingress:
                    ip = ingress[0].ip or ingress[0].hostname
                    if ip:
                        return ip
                time.sleep(5)
            raise TimeoutError(
                f"Service {service_name} never received a LoadBalancer IP within {timeout_seconds}s."
            )
        finally:
            Path(kubeconfig_path).unlink(missing_ok=True)

    return await loop.run_in_executor(None, _wait_for_ip)


async def delete_manifest_objects(kubeconfig_yaml: str, manifest_yaml: str) -> None:
    """Best-effort delete of Secret/Deployment/Service objects for teardown."""
    loop = asyncio.get_event_loop()

    def _delete() -> None:
        from kubernetes import client, config
        from kubernetes.client.exceptions import ApiException

        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
            tmp.write(kubeconfig_yaml)
            kubeconfig_path = tmp.name

        try:
            config.load_kube_config(config_file=kubeconfig_path)
            core_v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()

            for doc in yaml.safe_load_all(manifest_yaml):
                if doc is None:
                    continue
                namespace = doc["metadata"].get("namespace", "default")
                name = doc["metadata"]["name"]
                kind = doc["kind"]

                try:
                    if kind == "Deployment":
                        apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
                    elif kind == "Service":
                        core_v1.delete_namespaced_service(name=name, namespace=namespace)
                    elif kind == "Secret":
                        core_v1.delete_namespaced_secret(name=name, namespace=namespace)
                except ApiException as exc:
                    if exc.status == 404:
                        continue
                    raise
        finally:
            Path(kubeconfig_path).unlink(missing_ok=True)

    await loop.run_in_executor(None, _delete)


__all__ = [
    "apply_objects",
    "wait_deployment_available",
    "get_service_lb_ip",
    "delete_manifest_objects",
]
