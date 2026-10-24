"""Локальная генерация крупных QR-кодов высокого качества."""

from __future__ import annotations

from io import BytesIO

import segno


MAX_QR_BYTES = 1200
TARGET_QR_PIXELS = 1024


class QrCodeError(ValueError):
    """Данные не подходят для создания QR-кода."""


def generate_qr_png(content: str) -> bytes:
    """Создать чёткий PNG с коррекцией ошибок H и размером около 1024 px."""
    content = content.strip()
    if not content:
        raise QrCodeError("отправьте непустой текст для QR-кода")
    if len(content.encode("utf-8")) > MAX_QR_BYTES:
        raise QrCodeError(f"сократите данные до {MAX_QR_BYTES} байт")

    try:
        qr = segno.make(
            content,
            error="h",
            micro=False,
            boost_error=False,
        )
        base_width, _ = qr.symbol_size(scale=1, border=4)
        scale = max(6, min(32, TARGET_QR_PIXELS // base_width))

        output = BytesIO()
        qr.save(
            output,
            kind="png",
            scale=scale,
            border=4,
            dark="#000000",
            light="#FFFFFF",
        )
        return output.getvalue()
    except (ValueError, OverflowError) as exc:
        raise QrCodeError("данные слишком длинные или имеют неверный формат") from exc
