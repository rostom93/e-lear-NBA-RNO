"""Chatbot reply engine — keyword simulation with optional LLM hook."""

from django.conf import settings


KEYWORD_REPLIES = [
    (
        ("bonjour", "hello", "salut", "hi"),
        "Bonjour ! Je suis l'assistant e-learning. Posez-moi une question sur les cours, crédits ou votre progression.",
    ),
    (
        ("crédit", "credit", "pack", "acheter", "buy"),
        "Pour acheter des crédits, ouvrez la section Paiements et choisissez un pack. Les crédits sont ajoutés immédiatement en cas de succès.",
    ),
    (
        ("cours", "course", "catalogue", "catalog"),
        "Le catalogue liste les cours actifs. Filtrez par tags (#Angular, #Python, #AI), catégorie, niveau ou type de contenu.",
    ),
    (
        ("inscription", "enroll", "s'inscrire"),
        "L'inscription à un cours déduit automatiquement le prix en crédits. Vérifiez votre solde avant de vous inscrire.",
    ),
    (
        ("quiz", "progression", "progress"),
        "Complétez les modules et réussissez les quiz pour faire progresser votre barre de complétude.",
    ),
    (
        ("aide", "help", "support"),
        "Je peux vous guider sur les cours, les crédits et la progression. Reformulez votre question avec un mot-clé clair.",
    ),
]

DEFAULT_REPLY = (
    "Je n'ai pas bien compris. Essayez des mots-clés comme : cours, crédits, inscription, quiz, aide."
)


def generate_reply(message: str, user=None) -> str:
    """
    Return a chatbot reply.
    If LLM_API_KEY is set, this is the extension point for a real provider.
    """
    if settings.LLM_API_KEY and settings.LLM_API_URL:
        # Extension point for a real LLM — kept optional / unused without a key.
        return _call_llm_placeholder(message)

    text = (message or "").lower()
    for keywords, reply in KEYWORD_REPLIES:
        if any(k in text for k in keywords):
            return reply
    return DEFAULT_REPLY


def _call_llm_placeholder(message: str) -> str:
    """
    Placeholder for future LLM integration.
    Without a wired client, fall back to keyword matching.
    """
    text = (message or "").lower()
    for keywords, reply in KEYWORD_REPLIES:
        if any(k in text for k in keywords):
            return reply
    return DEFAULT_REPLY
