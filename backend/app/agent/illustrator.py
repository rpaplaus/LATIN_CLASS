import hashlib
import logging
from pathlib import Path
from typing import Any

from app.schemas.flashcard import FlashcardItem
from app.services.tts import get_or_create_latin_tts

logger = logging.getLogger(__name__)

IMAGES_STORAGE_DIR = (
    Path(__file__).resolve().parent.parent.parent / "storage" / "images"
)
IMAGES_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _generate_classical_roman_svg(
    word: str,
    translation: str,
    grammatical_class: str,
) -> str:
    """Generate a rich, museum-grade classical Roman medallion SVG artwork for a vocabulary term."""
    clean_word = word.strip().upper()
    clean_trans = translation.strip()

    # Roman imperial Tyrian crimson and antique gold aesthetic
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="100%" height="100%">
  <defs>
    <radialGradient id="marbleGrad" cx="50%" cy="50%" r="50%" fx="30%" fy="30%">
      <stop offset="0%" stop-color="#2a1218" />
      <stop offset="60%" stop-color="#19090c" />
      <stop offset="100%" stop-color="#0e0406" />
    </radialGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f6d365" />
      <stop offset="40%" stop-color="#d4af37" />
      <stop offset="70%" stop-color="#aa771c" />
      <stop offset="100%" stop-color="#805a1b" />
    </linearGradient>
    <filter id="goldGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Roman Stone Medallion Frame -->
  <rect width="600" height="600" rx="24" fill="url(#marbleGrad)" />
  <circle cx="300" cy="300" r="270" fill="none" stroke="url(#goldGrad)" stroke-width="6" opacity="0.85" />
  <circle cx="300" cy="300" r="255" fill="none" stroke="url(#goldGrad)" stroke-width="2" stroke-dasharray="8 6" opacity="0.6" />

  <!-- Classical Roman Header Inscription -->
  <text x="300" y="90" font-family="'Cinzel', 'Trajan Pro', 'Times New Roman', Georgia, serif" font-size="16" fill="#c5a059" font-weight="600" letter-spacing="6" text-anchor="middle">
    • SENATUS POPULUSQUE ROMANUS •
  </text>

  <!-- Roman Laurels Emblem Icon -->
  <g transform="translate(300, 200) scale(1.1)">
    <circle cx="0" cy="0" r="64" fill="#200a10" stroke="url(#goldGrad)" stroke-width="3" filter="url(#goldGlow)" />
    <!-- Classical Eagle / Laurel Silhouette Motif -->
    <path d="M-30,-15 C-45,-40 -15,-50 0,-30 C15,-50 45,-40 30,-15 C45,15 20,45 0,40 C-20,45 -45,15 -30,-15 Z" fill="url(#goldGrad)" opacity="0.9" />
    <polygon points="0,-18 12,-3 28,-3 15,7 20,22 0,12 -20,22 -15,7 -28,-3 -12,-3" fill="#fdf0cd" />
  </g>

  <!-- Central Latin Word -->
  <text x="300" y="340" font-family="'Cinzel', 'Trajan Pro', 'Times New Roman', Georgia, serif" font-size="44" font-weight="bold" fill="url(#goldGrad)" letter-spacing="4" text-anchor="middle" filter="url(#goldGlow)">
    {clean_word}
  </text>

  <!-- Grammatical Classification -->
  <text x="300" y="385" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" fill="#9ca3af" font-style="italic" text-anchor="middle">
    {grammatical_class}
  </text>

  <!-- Translation Pill -->
  <g transform="translate(300, 450)">
    <rect x="-190" y="-24" width="380" height="48" rx="24" fill="#2d1319" stroke="url(#goldGrad)" stroke-width="1.5" />
    <text x="0" y="7" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="19" font-weight="600" fill="#fef3c7" text-anchor="middle">
      "{clean_trans}"
    </text>
  </g>

  <!-- Antiquity Footnote -->
  <text x="300" y="555" font-family="'Cinzel', Georgia, serif" font-size="13" fill="#846332" letter-spacing="3" text-anchor="middle">
    ACADEMIA LATIUM • VOCABULARIUM CANONICUM
  </text>
</svg>"""
    return svg


async def create_flashcard_for_word(
    word: str,
    dictionary_entry: str,
    grammatical_class: str,
    translation: str,
    example_sentence: str,
    redis_client: Any | None = None,
) -> FlashcardItem:
    """Generate a multimodal Latin flashcard complete with authentic Roman illustration and audio pronunciation."""
    # 1. Generate or retrieve TTS Audio
    audio_bytes, audio_hash, audio_b64, _ = await get_or_create_latin_tts(
        text=word,
        voice="onyx",
        redis_client=redis_client,
    )

    # 2. Generate Image Illustration
    image_hash = hashlib.sha256(
        f"card:{word.strip().lower()}:{translation.strip().lower()}".encode()
    ).hexdigest()
    image_filename = f"{image_hash}.svg"
    image_path = IMAGES_STORAGE_DIR / image_filename

    # If image does not exist in storage, generate it
    if not image_path.exists():
        svg_content = _generate_classical_roman_svg(
            word=word,
            translation=translation,
            grammatical_class=grammatical_class,
        )
        try:
            image_path.write_text(svg_content, encoding="utf-8")
            logger.info(
                "Generated classical flashcard artwork for '%s' (%s)", word, image_hash
            )
        except Exception as exc:
            logger.warning("Failed to save SVG image (%s): %s", image_path, exc)

    image_url = f"/api/v1/media/images/{image_filename}"
    audio_url = f"/api/v1/media/audio/{audio_hash}"

    return FlashcardItem(
        id=f"card-{image_hash[:12]}",
        word=word.strip(),
        dictionary_entry=dictionary_entry.strip(),
        grammatical_class=grammatical_class.strip(),
        translation=translation.strip(),
        example_sentence=example_sentence.strip(),
        image_url=image_url,
        audio_url=audio_url,
        audio_base64=audio_b64,
    )
