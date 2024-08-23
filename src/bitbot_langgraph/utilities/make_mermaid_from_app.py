# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)

def make_mermaid_from_app(app, path="app.md", logger=None):
    logger = logger or logging.getLogger(__name__)
    logger.info(f"make_mermaid_from_app: {path}")

    mermaid_text = app.get_graph().draw_mermaid()
    logger.debug(f"mermaid_text: {mermaid_text}")

    output_markdown = f"""
```mermaid
{mermaid_text}
```
"""
    # replace contents
    with open(path, "w") as f:
        f.write(output_markdown)

    response = {
        "path": path,
        "mermaid_text": mermaid_text,
        "output_markdown": output_markdown
    }
    logger.debug(f"response: {response}")
    return response