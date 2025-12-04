import json
import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator, Dict, List

import gradio as gr
from core.analyzer import DocumentAnalyzer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("app.log"),  # Log to file
    ],
)
logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.analyzer = DocumentAnalyzer()
        # Get valid question IDs from the loaded questions
        self.valid_question_ids = list(
            range(1, len(self.analyzer.questions["TCFD Analysis"]["questions"]) + 1)
        )
        logger.info(
            f"Initialized with {len(self.valid_question_ids)} valid question IDs"
        )

    def validate_question_ids(self, question_ids: List[int]) -> List[int]:
        """Validate and filter question IDs"""
        if not question_ids:
            raise ValueError("No questions selected")

        valid_ids = [qid for qid in question_ids if qid in self.valid_question_ids]
        if not valid_ids:
            raise ValueError("No valid questions selected")

        logger.info(f"Validated question IDs: {valid_ids}")
        return valid_ids

    async def process_document(
        self, file_path: str, question_ids: List[int] = None
    ) -> AsyncGenerator[Dict, None]:
        """Process uploaded document and stream analysis results"""
        if not file_path:
            yield {"error": "No file uploaded"}
            return

        try:
            # Validate question IDs only if they are provided
            if question_ids is not None:
                question_ids = self.validate_question_ids(question_ids)
                logger.info(f"Processing questions: {question_ids}")
            else:
                # If no questions specified, use all valid IDs
                question_ids = self.valid_question_ids
                logger.info("No questions specified, using all questions")

            temp_file = Path(tempfile.gettempdir()) / f"temp_{uuid.uuid4()}.pdf"
            try:
                shutil.copy2(file_path, temp_file)
                async for result in self.analyzer.process_document(
                    str(temp_file), question_ids
                ):
                    logger.info(
                        f"Processing section: {result.get('section', 'unknown')}"
                    )
                    yield result
            finally:
                if temp_file.exists():
                    temp_file.unlink()
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            yield {"error": f"Failed to process document: {str(e)}"}


def create_app():
    service = DocumentService()
    progress_tracker = gr.Progress()

    with gr.Blocks(
        title="TCFD Report Analyzer",
        theme=gr.themes.Soft(),
        css="""
        .question-result {
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .question-result h3 {
            margin-top: 0;
        }
    """,
    ) as app:
        gr.Markdown("# TCFD Report Analyzer")

        with gr.Tabs() as tabs:
            # Analysis Tab
            with gr.Tab("Analysis"):
                gr.Markdown("Upload a sustainability report for detailed TCFD analysis")

                with gr.Row():
                    file_input = gr.File(
                        label="Upload PDF Report", file_types=[".pdf"], type="filepath"
                    )
                    analyze_btn = gr.Button("Start Analysis", variant="primary")

                with gr.Row():
                    progress = gr.Markdown("Upload a report to begin analysis")

                # Results Section
                with gr.Column(visible=False) as results_container:
                    with gr.Row():
                        gr.Markdown("## Analysis Results")

                    # Accordion for each question
                    questions_accordion = gr.Accordion("Questions", open=False)

                    # DataFrame for summary view
                    summary_df = gr.Dataframe(
                        headers=["Question", "Score", "Answer Summary"],
                        label="Analysis Summary",
                        visible=False,
                    )

            # Questions Tab
            with gr.Tab("Questions"):
                gr.Markdown("## TCFD Questions")
                gr.Markdown("Select which questions to include in the analysis")

                with gr.Row():
                    select_all = gr.Button("Select All", variant="secondary")
                    clear_all = gr.Button("Clear All", variant="secondary")

                questions = service.analyzer.questions["TCFD Analysis"]["questions"]
                checkboxes = []

                for i, question in enumerate(questions, 1):
                    checkbox = gr.Checkbox(
                        label=f"Q{i}: {question}",
                        value=True,  # Default to selected
                        interactive=True,
                    )
                    checkboxes.append(checkbox)

        async def process_analysis(file, *selected_questions):
            results_container.visible = False
            summary_data = []

            if not file:
                yield "Please upload a file first", [], {}
                return

            try:
                selected_ids = [
                    i + 1 for i, selected in enumerate(selected_questions) if selected
                ]
                if not selected_ids:
                    yield "Please select at least one question", [], {}
                    return

                questions_html = ""

                async for result in service.process_document(file, selected_ids):
                    if "error" in result:
                        yield f"Error: {result['error']}", [], {}
                        return

                    if "status" in result:
                        progress_tracker(0, desc=result["status"])
                        continue

                    try:
                        analysis = json.loads(result["result"])

                        # Create accordion item for this question
                        score_html = f'<div style="background-color: #FFA500; padding: 5px; display: inline-block; border-radius: 4px;">Score: {analysis.get("score", "N/A")}</div>'

                        question_html = f"""
                        <div class="question-result">
                            <h3>Question {result['question_number']}</h3>
                            {score_html}
                            <p><strong>Q:</strong> {result['question']}</p>
                            <p><strong>A:</strong> {analysis.get('answer', 'No answer provided')}</p>
                        """

                        if analysis.get("evidence"):
                            question_html += "<p><strong>Evidence:</strong></p><ul>"
                            question_html += "".join(
                                [f"<li>{e}</li>" for e in analysis["evidence"]]
                            )
                            question_html += "</ul>"

                        if analysis.get("gaps"):
                            question_html += "<p><strong>Gaps:</strong></p><ul>"
                            question_html += "".join(
                                [f"<li>{g}</li>" for g in analysis["gaps"]]
                            )
                            question_html += "</ul>"

                        question_html += "</div>"
                        questions_html += question_html

                        # Add to summary data
                        summary_data.append(
                            [
                                f"Q{result['question_number']}",
                                analysis.get("score", "N/A"),
                                analysis.get("answer", "No answer")[:100] + "...",
                            ]
                        )

                        # Update UI
                        results_container.visible = True
                        yield questions_html, summary_data, {"visible": True}

                    except json.JSONDecodeError:
                        logger.error("Failed to parse analysis result")
                        continue

                progress_tracker(1.0, desc="Analysis complete!")

            except Exception as e:
                logger.error(f"Error in analysis: {str(e)}", exc_info=True)
                yield f"Error: {str(e)}", [], {}

        def select_all_questions():
            """Select all questions"""
            logger.info("Selecting all questions")
            return [True] * len(checkboxes)

        def clear_all_questions():
            """Clear all question selections"""
            logger.info("Clearing all questions")
            return [False] * len(checkboxes)

        # Connect components
        analyze_btn.click(
            fn=process_analysis,
            inputs=[file_input] + checkboxes,
            outputs=[questions_accordion, summary_df, results_container],
        )

        select_all.click(fn=select_all_questions, inputs=[], outputs=checkboxes)

        clear_all.click(fn=clear_all_questions, inputs=[], outputs=checkboxes)

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=True, debug=True)
