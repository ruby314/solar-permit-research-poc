import os
import zipfile
from dotenv import load_dotenv
import gradio as gr
from md2pdf.core import md2pdf
from main_agent import create_main_agent
from typing import Iterable


def create_zip_archive(file_paths: Iterable[str], output_zip_path: str) -> None:
    """Utility function for zipping multiple files into a zip archive"""

    with zipfile.ZipFile(output_zip_path, "w") as zipf:
        for file_path in file_paths:
            zipf.write(file_path, os.path.basename(file_path))


def generate_document(input_address: str, uploaded_file: gr.utils.NamedString):
    print(f"Processing: {input_address}")

    # create and invoke agent
    agent = create_main_agent(document_path=uploaded_file)
    result = agent.invoke({"user_input": input_address})

    # write research to pdf file
    research_path = "research_summary.pdf"
    md2pdf(research_path, result["research_result"])

    # combine with saved permit json
    zip_path = "output.zip"
    files_to_zip = [research_path]
    if result["permit_json_path"] != "":
        files_to_zip += [result["permit_json_path"]]
    create_zip_archive(files_to_zip, zip_path)

    return zip_path


if __name__ == "__main__":

    load_dotenv(".env", override=True)

    with gr.Blocks() as demo:
        gr.Markdown("# Agent Demo")

        gr.Markdown(
            "Enter a project address, upload a PDF containing information for the permit, and click start."
        )
        gr.Markdown(
            "Created outputs will be available to download as a zip file (click the blue hyperlink showing file size at the right)."
        )

        with gr.Row():
            input_address = gr.Textbox(
                label="Project address:", lines=1, placeholder="Type here..."
            )
            file_input = gr.File(label="Upload a document (pdf)", file_types=[".pdf"])

        start_button = gr.Button("Start")

        output_file = gr.File(label="Download your generated document")

        clear_button = gr.ClearButton(
            components=[input_address, file_input, output_file]
        )

        start_button.click(
            fn=generate_document,
            inputs=[input_address, file_input],
            outputs=output_file,
        )

    demo.launch(share=True)
