import gradio as gr
from sendgrid.helpers.mail import Mail, Email, To, Content
import os
import openai
from .config import config
from .services import PaperService, EmailService
from .constants import get_topic_abbreviation
from .services.subjects import process_subject_fields


def sample(email, topic, physics_topic, categories, interest):
    if not topic:
        raise gr.Error("You must choose a topic.")
    if topic == "Physics":
        if isinstance(physics_topic, list):
            raise gr.Error("You must choose a physics topic.")
        topic = physics_topic
        abbr = get_topic_abbreviation(topic)
    else:
        abbr = get_topic_abbreviation(topic)
    if categories:
        papers = get_papers(abbr)
        papers = [
            t for t in papers
            if bool(set(process_subject_fields(t['subjects'])) & set(categories))][:4]
    else:
        papers = get_papers(abbr, limit=4)
    if interest:
        if not openai.api_key: raise gr.Error("Set your OpenAI api key on the left first")
        relevancy, _ = generate_relevance_score(
            papers,
            query={"interest": interest},
            threshold_score=0,
            num_paper_in_prompt=4)
        return "\n\n".join([paper["summarized_text"] for paper in relevancy])
    else:
        return "\n\n".join(f"Title: {paper['title']}\nAuthors: {paper['authors']}" for paper in papers)


def change_subsubject(subject, physics_subject):
    if subject != "Physics":
        return gr.Dropdown.update(choices=categories_map[subject], value=[], visible=True)
    else:
        if physics_subject and not isinstance(physics_subject, list):
            return gr.Dropdown.update(choices=categories_map[physics_subject], value=[], visible=True)
        else:
            return gr.Dropdown.update(choices=[], value=[], visible=False)


def change_physics(subject):
    if subject != "Physics":
        return gr.Dropdown.update(visible=False, value=[])
    else:
        return gr.Dropdown.update(physics_topics, visible=True)


def test(email, topic, physics_topic, categories, interest, key):
    if not email: raise gr.Error("Set your email")
    if not key: raise gr.Error("Set your SendGrid key")
    if topic == "Physics":
        if isinstance(physics_topic, list):
            raise gr.Error("You must choose a physics topic.")
        topic = physics_topic
        abbr = physics_topics[topic]
    else:
        abbr = topics[topic]
    if categories:
        papers = get_papers(abbr)
        papers = [
            t for t in papers
            if bool(set(process_subject_fields(t['subjects'])) & set(categories))][:4]
    else:
        papers = get_papers(abbr, limit=4)
    if interest:
        if not openai.api_key: raise gr.Error("Set your OpenAI api key on the left first")
        relevancy, hallucination = generate_relevance_score(
            papers,
            query={"interest": interest},
            threshold_score=7,
            num_paper_in_prompt=8)
        body = "<br><br>".join([f'Title: <a href="{paper["main_page"]}">{paper["title"]}</a><br>Authors: {paper["authors"]}<br>Score: {paper["Relevancy score"]}<br>Reason: {paper["Reasons for match"]}' for paper in relevancy])
        if hallucination:
            body = "Warning: the model hallucinated some papers. We have tried to remove them, but the scores may not be accurate.<br><br>" + body
    else:
        body = "<br><br>".join([f'Title: <a href="{paper["main_page"]}">{paper["title"]}</a><br>Authors: {paper["authors"]}' for paper in papers])
    sg = sendgrid.SendGridAPIClient(api_key=key)
    from_email = Email(email)
    to_email = To(email)
    subject = "arXiv digest"
    content = Content("text/html", body)
    mail = Mail(from_email, to_email, subject, content)
    mail_json = mail.get()

    # Send an HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    if response.status_code >= 200 and response.status_code <= 300:
        return "Success!"
    else:
        return "Failure: ({response.status_code})"


def register_openai_token(token):
    openai.api_key = token

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            token = gr.Textbox(label="OpenAI API Key", type="password")
            subject = gr.Radio(
                list(topics.keys()), label="Topic"
            )
            physics_subject = gr.Dropdown(physics_topics, value=[], multiselect=False, label="Physics category", visible=False, info="")
            subsubject = gr.Dropdown(
                    [], value=[], multiselect=True, label="Subtopic", info="Optional. Leaving it empty will use all subtopics.", visible=False)
            subject.change(fn=change_physics, inputs=[subject], outputs=physics_subject)
            subject.change(fn=change_subsubject, inputs=[subject, physics_subject], outputs=subsubject)
            physics_subject.change(fn=change_subsubject, inputs=[subject, physics_subject], outputs=subsubject)

            interest = gr.Textbox(label="A natural language description of what you are interested in. We will generate relevancy scores (1-10) and explanations for the papers in the selected topics according to this statement.", info="Press shift-enter or click the button below to update.", lines=7)
            sample_btn = gr.Button("Generate Digest")
            sample_output = gr.Textbox(label="Results for your configuration.", info="For runtime purposes, this is only done on a small subset of recent papers in the topic you have selected. Papers will not be filtered by relevancy, only sorted on a scale of 1-10.")
        with gr.Column(scale=0.40):
            with gr.Box():
                title = gr.Markdown(
                    """
                    # Email Setup, Optional
                    Send an email to the below address using the configuration on the right. Requires a sendgrid token. These values are not needed to use the right side of this page.

                    To create a scheduled job for this, see our [Github Repository](https://github.com/AutoLLM/ArxivDigest)
                    """,
                    interactive=False, show_label=False)
                email = gr.Textbox(label="Email address", type="email", placeholder="")
                sendgrid_token = gr.Textbox(label="SendGrid API Key", type="password")
                with gr.Row():
                    test_btn = gr.Button("Send email")
                    output = gr.Textbox(show_label=False, placeholder="email status")
    test_btn.click(fn=test, inputs=[email, subject, physics_subject, subsubject, interest, sendgrid_token], outputs=output)
    token.change(fn=register_openai_token, inputs=[token])
    sample_btn.click(fn=sample, inputs=[email, subject, physics_subject, subsubject, interest], outputs=sample_output)
    subject.change(fn=sample, inputs=[email, subject, physics_subject, subsubject, interest], outputs=sample_output)
    physics_subject.change(fn=sample, inputs=[email, subject, physics_subject, subsubject, interest], outputs=sample_output)
    subsubject.change(fn=sample, inputs=[email, subject, physics_subject, subsubject, interest], outputs=sample_output)
    interest.submit(fn=sample, inputs=[email, subject, physics_subject, subsubject, interest], outputs=sample_output)

demo.launch(show_api=False)
