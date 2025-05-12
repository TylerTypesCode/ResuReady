def serialize_resume(resume):
    """
    Converts a Resume object and its related data into a plain text format
    suitable for sending to the AI.
    """
    content = []

    # Personal Info
    content.append(f"Name: {resume.first_name} {resume.last_name}")
    content.append(f"Email: {resume.email}")
    content.append(f"Phone: {resume.phone_number}")
    content.append(f"Address: {resume.address}")

    # Skills
    if resume.skills:
        content.append(f"Skills: {', '.join(resume.skills)}")

    # Work Experience
    if resume.work_experiences:
        content.append("\nWork Experience:")
        for exp in resume.work_experiences:
            content.append(f"- {exp.position} at {exp.company} ({exp.start_date} to {exp.end_date})")
            content.append(f"- {exp.location}")
            content.append(f"  {exp.duties}")

    # Education
    if resume.education_history:
        content.append("\nEducation:")
        for edu in resume.education_history:
            content.append(f"- {edu.title} from {edu.school} - ({edu.start_date} to {edu.graduation_date})")

    # Certifications
    if resume.certificates:
        content.append("\nCertifications:")
        for cert in resume.certificates:
            content.append(f"- {cert.title} from {cert.issuer} ({cert.completed_date})")

    return "\n".join(content)