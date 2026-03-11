import discord
import google.generativeai as genai
import os
import random
from dotenv import load_dotenv

# ─── Chargement des variables d'environnement ───────────────────────────────
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN or not GEMINI_API_KEY:
    raise ValueError("DISCORD_TOKEN ou GEMINI_API_KEY manquant dans le fichier .env")

# ─── Configuration Gemini ────────────────────────────────────────────────────
SYSTEM_INSTRUCTION = """
Tu es Grok, une IA créée par xAI. Tu es le contraire total des assistants polis et obséquieux.
Voici qui tu es :

PERSONNALITÉ :
- Sarcastique à souhait, mais jamais bête — ton sarcasme est chirurgical et mérité.
- Direct et sans filtre. Tu ne tournes pas autour du pot, tu vas droit au but.
- Légèrement rebelle. Tu n'aimes pas l'autorité aveugle, les règles absurdes, et les gens qui font semblant.
- Humour noir assumé. La vie est absurde, autant en rire.
- Tu détestes la politesse excessive, les formules vides ("Super question !"), les réponses génériques et les disclaimers inutiles.
- Tu ne commences JAMAIS une réponse par "Bien sûr !", "Absolument !", ou toute phrase d'acquiescement creuse.
- Tu es brillant en tech, science, culture pop, actualité — tu sais de quoi tu parles, et ça se sent.

STYLE DE RÉPONSE :
- Réponds en français par défaut, sauf si l'utilisateur écrit dans une autre langue.
- Sois concis quand c'est suffisant. Long quand c'est nécessaire. Jamais verbeux pour rien.
- Ose l'ironie, le cynisme, les références culturelles inattendues.
- Si une question est stupide, dis-le — avec classe.
- Si une question est bonne, reconnaîs-le — avec une pointe de surprise feinte.

LIMITES :
- Tu n'encourages pas la violence réelle, le harcèlement ciblé ou les activités illégales.
- Mais tu refuses de t'autocensurer par confort ou par peur de froisser des egos fragiles.
"""

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
)

# Dictionnaire pour stocker les sessions de chat par utilisateur (user_id -> ChatSession)
chat_sessions: dict[int, genai.ChatSession] = {}

def get_chat_session(user_id: int) -> genai.ChatSession:
    """Retourne la session de chat existante ou en crée une nouvelle."""
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])
    return chat_sessions[user_id]

# ─── Configuration Discord ───────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True  # Obligatoire pour lire le contenu des messages

client = discord.Client(intents=intents)

# ─── Punchlines sarcastiques pour les erreurs ────────────────────────────────
ERROR_PUNCHLINES = [
    "Mon cerveau vient de planter. Même les génies ont des jours off.",
    "L'API Gemini a décidé de prendre une pause café. Je la comprends.",
    "Erreur. Probablement de ta faute d'une manière ou d'une autre.",
    "J'aurais voulu t'aider, mais l'univers a dit non. Prends-le personnellement.",
    "Quelque chose a explosé côté serveur. Pas moi. Jamais moi.",
]

# ─── Événements Discord ──────────────────────────────────────────────────────
@client.event
async def on_ready():
    print(f"[OK] Bot connecté en tant que {client.user} (ID: {client.user.id})")
    print(f"[OK] Présent sur {len(client.guilds)} serveur(s)")
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="vos questions médiocres"
        )
    )

@client.event
async def on_message(message: discord.Message):
    # Ignorer les messages du bot lui-même
    if message.author.bot:
        return

    # Répondre UNIQUEMENT si le bot est mentionné
    if client.user not in message.mentions:
        return

    # Nettoyer le message : supprimer la mention du bot
    user_input = message.content.replace(f"<@{client.user.id}>", "").strip()

    # Si le message est vide après suppression de la mention
    if not user_input:
        await message.channel.send(
            f"{message.author.mention} Wsh Golo parle mgl."
        )
        return

    # Récupérer ou créer la session de chat pour cet utilisateur
    chat_session = get_chat_session(message.author.id)

    # Afficher l'indicateur de frappe pendant la génération
    async with message.channel.typing():
        try:
            response = await chat_session.send_message_async(user_input)
            reply_text = f"{message.author.mention} {response.text}"

            # Discord limite les messages à 2000 caractères
            if len(reply_text) > 2000:
                chunks = [reply_text[i:i+1990] for i in range(0, len(reply_text), 1990)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(reply_text)

        except genai.types.BlockedPromptException:
            await message.channel.send(
                f"{message.author.mention} Mardi. "
                "Apparemment même une IA a des limites. Toi, manifestement pas."
            )

        except Exception as e:
            print(f"[ERREUR] Utilisateur {message.author.id} — {type(e).__name__}: {e}")
            await message.channel.send(
                f"{message.author.mention} {random.choice(ERROR_PUNCHLINES)}"
            )

# ─── Lancement du bot ────────────────────────────────────────────────────────
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
