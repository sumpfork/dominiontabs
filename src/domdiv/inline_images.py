import re

from . import resource_handling


def expand_wiki_nowrap_template(s: str) -> str:
    return re.sub(r"{{nowrap\|([^{}]+)}}", r"<nobr>\1</nobr>", s)


def nobr(s: str) -> str:
    return f"<nobr>{s}</nobr>"


def nobr_if_necessary(s: str, needed: bool) -> str:
    if needed:
        return nobr(s)
    else:
        return s


class InlineImage(object):
    def __init__(self, width, height, valign):
        self.width = width
        self.height = height
        self.valign = valign


class CoinInlineImage(InlineImage):
    def __init__(self, width, height, valign, resolution):
        super().__init__(width, height, valign)
        if resolution == "low":
            # TODO: unlike the other low-res images, the empty coin doesn't have extra whitespace on the right,
            # so it looks squashed when rendered at the aspect ratio that works for the others. It would be good to
            # clean them all up at some point.
            self.blank_image = "coin_small_empty.png"
            self.question_image = "coin_small_question.png"
            self.x_image = "coin_small_x.png"
            self.n_image = "coin_small_{n}.png"
        elif resolution == "medium":
            self.blank_image = "coin.png"
            self.question_image = "coin_small_question.png"
            self.x_image = "coin_small_x.png"
            self.n_image = "coin_small_{n}.png"
        elif resolution == "high":
            self.blank_image = "highres/Coin.png"
            self.question_image = "highres/CoinQ.png"
            self.x_image = "highres/Coinx.png"
            self.n_image = "highres/Coin{n}.png"
        else:
            raise Exception(f"CoinScale: Unsupported resolution: {resolution}")

    def coin(self, coins, fontsize):
        if coins and coins.isdigit():
            coin_image = self.n_image.format(n=int(coins))
        elif coins in {"x", "X"}:
            coin_image = self.x_image
        elif coins == "?":
            coin_image = self.question_image
        else:
            coin_image = self.blank_image
        image_path = str(resource_handling.get_image_filepath(coin_image))
        width = self.width * fontsize
        height = self.height * fontsize
        return f'<img src="{image_path}" width="{width}" height="{height}" valign="{self.valign}" />'


class DebtInlineImage(InlineImage):
    def __init__(self, width, height, valign, resolution):
        super().__init__(width, height, valign)
        if resolution == "low":
            self.blank_image = "debt.png"
            self.n_image = "debt_{n}.png"
        elif resolution in ["medium", "high"]:
            self.blank_image = "highres/Debt.png"
            self.n_image = "highres/Debt{n}.png"
        else:
            raise Exception(f"DebtScale: Unsupported resolution: {resolution}")

    def debt(self, debt, fontsize):
        if debt and debt.isdigit():
            debt_image = self.n_image.format(n=int(debt))
        else:
            debt_image = self.blank_image
        image_path = str(resource_handling.get_image_filepath(debt_image))
        width = self.width * fontsize
        height = self.height * fontsize
        return f'<img src="{image_path}" width="{width}" height="{height}" valign="{self.valign}" />'


class SimpleInlineImage(InlineImage):
    def __init__(self, width, height, valign, image: str):
        super().__init__(width, height, valign)
        self.image = image


class PotionInlineImage(SimpleInlineImage):
    def potion(self, fontsize):
        image_path = str(resource_handling.get_image_filepath(self.image))
        width = self.width * fontsize
        height = self.height * fontsize
        return f'<img src="{image_path}" width="{width}" height="{height}" valign="{self.valign}" />'


class VpInlineImage(SimpleInlineImage):
    def __init__(self, width, height, valign, image: str, fontsize_multiplier):
        SimpleInlineImage.__init__(self, width, height, valign, image)
        self.fontsize_multiplier = fontsize_multiplier

    def vp(self, vp, fontsize):
        image_path = str(resource_handling.get_image_filepath(self.image))
        width = self.width * fontsize
        height = self.height * fontsize
        img = f'<img src="{image_path}" width="{width}" height="{height}" valign="{self.valign}" />'
        if vp:
            return nobr(
                f"<b><font size={fontsize * self.fontsize_multiplier}>{vp}</font></b>{img}"
            )
        return img


class SunInlineImage(SimpleInlineImage):
    def sun(self, fontsize):
        image_path = str(resource_handling.get_image_filepath(self.image))
        width = self.width * fontsize
        height = self.height * fontsize
        return f'<img src="{image_path}" width="{width}" height="{height}" valign="{self.valign}" />'

    def sunplus(self, fontsize):
        image_path = str(resource_handling.get_image_filepath(self.image))
        width = self.width * fontsize
        height = self.height * fontsize
        return nobr(
            f'<b>+1</b><img src="{image_path}" width="{width}" height="{height}" valign="{self.valign}" />'
        )


class InlineImages(object):
    def __init__(
        self,
        coin: dict[str, CoinInlineImage],
        potion: dict[str, PotionInlineImage],
        vp: dict[str, VpInlineImage],
        debt: dict[str, DebtInlineImage],
        sun: dict[str, SunInlineImage],
    ):
        self.coin = coin
        self.potion = potion
        self.vp = vp
        self.debt = debt
        self.sun = sun


IMAGES = InlineImages(
    coin={
        "m": CoinInlineImage(1.2, 1, valign="-28%", resolution="low"),
        "l": CoinInlineImage(2.4, 2.2, valign="top", resolution="medium"),
        "xl": CoinInlineImage(5, 5, valign="top", resolution="medium"),
    },
    potion={
        "m": PotionInlineImage(1.2, 1, valign="middle", image="potion_small.png"),
        "l": PotionInlineImage(2, 1.4, valign="top", image="potion_small.png"),
        "xl": PotionInlineImage(3, 4, valign="top", image="highres/Potion.png"),
    },
    vp={
        "m": VpInlineImage(
            1.25, 1, valign="middle", image="victory_emblem.png", fontsize_multiplier=1
        ),
        "l": VpInlineImage(
            2, 2.4, valign="middle", image="highres/VP.png", fontsize_multiplier=3
        ),
        "xl": VpInlineImage(
            3.4, 4, valign="-10%", image="highres/VP.png", fontsize_multiplier=5
        ),
    },
    debt={
        "m": DebtInlineImage(1.2, 1.05, valign="-28%", resolution="low"),
    },
    sun={
        "m": SunInlineImage(1.2, 1.2, valign="middle", image="sun.png"),
    },
)


def replace_wiki_templates(text, fontsize):
    def replace_cost_template(match: re.Match):
        """
        Handles the {{Cost}} and {{Costplus}} wiki templates, which each have up to four parameters:
        {{Cost|coins|size|debt|potion}}
        All parameters are optional.
        If the template name is Costplus a bold plus sign is prepended with no line break between it and the image.
        {{Cost}} means a single blank coin icon. Otherwise, the coin icon is omitted unless the coins parameter is
        non-empty.
        If debt or coins are a number, that number is put inside the icon.
        If debt or coins are '-', then the blank debt/coin icon is rendered.
        If coins is "x" or "?" then the special x or ? coins icon is rendered.
        If the potion parameter is "P" then a single potion is added at the end.
        If not specified, size defaults to "m", which is the regular size for embedded text in cards.
        Size "l" is used for e.g. kingdom treasures that have a larger symbol and also other text, like Hoard.
        Size "xl" is used for the base cards that have no other text, like Silver.
        """
        coin = None
        size = None
        debt = ""
        potion = ""
        prefix = ""
        needs_nobr_tag = False
        if match:
            if match.group(2):
                prefix = "+"
                needs_nobr_tag = True
            if match.group(3):
                parts = match.group(3).split("|")
                coin = parts[1] if len(parts) > 1 else ""
                size = parts[2] if len(parts) > 2 else ""
                debt = parts[3] if len(parts) > 3 else ""
                potion = parts[4] if len(parts) > 4 else ""
            else:
                # A completely empty template is a blank coin
                return nobr_if_necessary(
                    f"{prefix}{IMAGES.coin['m'].coin('-', fontsize)}", needs_nobr_tag
                )
        size = size or "m"  # medium is the default size
        if potion == "P":
            potion = IMAGES.potion[size].potion(fontsize)
        if debt:
            debt = IMAGES.debt[size].debt(debt, fontsize)

        if coin == "" and (potion or debt):
            return nobr_if_necessary("".join([prefix, debt, potion]), needs_nobr_tag)
        coin = IMAGES.coin[size].coin(coin, fontsize)
        if debt or potion:
            needs_nobr_tag = True
        return nobr_if_necessary("".join([prefix, coin, debt, potion]), needs_nobr_tag)

    def handle_match(match: re.Match):
        prefix = ""
        size = None
        count = None
        debt = ""
        potion = ""
        template = match.group(1)
        if template.lower() == "cost":
            return replace_cost_template(match)
        if match.group(2):
            prefix = "+"
        if match.group(3):
            parts = match.group(3).split("|")
            count = parts[1] if len(parts) > 1 else ""
            size = parts[2] if len(parts) > 2 else "m"
            debt = parts[3] if len(parts) > 3 else ""
            potion = parts[4] if len(parts) > 4 else ""

        size = size or "m"
        if template == "VP":
            return IMAGES.vp[size].vp(count, fontsize)
        if template.lower() == "debt":
            debt_img = IMAGES.debt[size].debt(count, fontsize)
            if prefix:
                return nobr(f"<b>{prefix}</b>{debt_img}")
            return debt_img
        if template.lower() == "sun":
            scale = IMAGES.sun[size]
            if prefix == "+":
                return scale.sunplus(fontsize)
            else:
                return scale.sun(fontsize)

        raise ValueError("Unknown template")

    return re.sub(
        r"{{([Cc]ost|[Dd]ebt|VP|[Ss]un)(plus)?(\|[^}]*?)?}}", handle_match, text
    )
