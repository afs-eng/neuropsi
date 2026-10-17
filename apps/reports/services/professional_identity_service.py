class ProfessionalIdentityService:
    @staticmethod
    def author_label(report) -> str:
        evaluation = getattr(report, "evaluation", None)
        author = getattr(evaluation, "examiner", None) or getattr(report, "author", None)
        if author is None:
            return "Profissional não informado"
        name = (getattr(author, "full_name", "") or "").strip()
        if not name:
            name = author.get_full_name().strip() if hasattr(author, "get_full_name") else ""
        name = name or getattr(author, "username", "") or "Profissional não informado"
        crp = (getattr(author, "crp", "") or "").strip()
        return f"{name} (CRP {crp})" if crp else name
