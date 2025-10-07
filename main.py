import argparse
from dotenv import load_dotenv
from md2pdf.core import md2pdf
from main_agent import create_main_agent

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", type=str, help="project address")
    parser.add_argument(
        "--pdf_path",
        type=str,
        help="path to PDF containing info to be extracted for permit",
    )
    args = parser.parse_args()

    load_dotenv(".env", override=True)

    agent = create_main_agent(document_path=args.pdf_path)
    result = agent.invoke({"user_input": args.address})

    research_path = "research_summary.pdf"
    md2pdf(research_path, result["research_result"])

    output_files = [research_path]
    if result["permit_json_path"] != "":
        output_files += [result["permit_json_path"]]

    for fpath in output_files:
        print(f"created {fpath}")
