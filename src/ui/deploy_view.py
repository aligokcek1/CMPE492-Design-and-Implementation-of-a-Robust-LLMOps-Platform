import streamlit as st

from src.cache import ModelCache

_MOCKED_RESPONSE = (
    "[Mocked Inference] Input: '{prompt}' → "
    "Response: 'This is a simulated response from model {model_name}.'"
)


def render():
    """Render the Deployment and Mocked Inference UI."""
    st.header("Deploy & Test Models")

    cache = ModelCache()
    models = cache.get_all_models()

    if not models:
        st.info("No models registered yet. Upload a model first.")
        return

    for model in models:
        with st.expander(f"**{model['name']}** — `{model['hf_repo_id']}`"):
            st.write(f"**Source**: {model['source_type']}")
            st.write(f"**Deployed**: {'Yes' if model['is_deployed'] else 'No'}")

            if not model["is_deployed"]:
                if st.button("Deploy to Cloud", key=f"deploy_{model['hf_repo_id']}"):
                    cache.mark_as_deployed(model["hf_repo_id"])
                    st.success(
                        f"Model `{model['name']}` deployed successfully to the mocked GCP environment."
                    )
                    st.rerun()
            else:
                st.write(f"**Deployed at**: {model['deployed_at']}")
                st.subheader("Test Inference")
                prompt = st.text_input("Enter a prompt", key=f"prompt_{model['hf_repo_id']}")
                if st.button("Run Inference", key=f"infer_{model['hf_repo_id']}"):
                    if not prompt.strip():
                        st.error("Please enter a prompt.")
                    else:
                        st.info(
                            _MOCKED_RESPONSE.format(
                                prompt=prompt.strip(),
                                model_name=model["name"],
                            )
                        )
