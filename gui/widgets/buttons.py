import customtkinter as ctk
from PIL import Image
from gui.config import constants as config


# =====================================================================
# Preset colour / style definitions
# =====================================================================

_PRESETS = {
    # ---- solid fills ----
    "primary": {
        "fg_color": config.COLOR_ACCENT,
        "hover_color": config.COLOR_ACCENT_HOVER,
    },
    "success": {
        "fg_color": config.COLOR_SUCCESS,
        "hover_color": config.COLOR_SUCCESS_HOVER,
    },
    "error": {
        "fg_color": config.COLOR_ERROR,
        "hover_color": config.COLOR_ERROR_HOVER,
    },
    "danger": {
        "fg_color": config.COLOR_ERROR,
        "hover_color": config.COLOR_ERROR_HOVER,
    },
    "secondary": {
        "fg_color": config.COLOR_SECONDARY_BUTTON,
        "hover_color": config.COLOR_SECONDARY_BUTTON_HOVER,
    },
    "highlight": {
        "fg_color": config.COLOR_HIGHLIGHT,
        "hover_color": config.COLOR_ACCENT_HOVER,
    },
    "neutral": {
        "fg_color": config.COLOR_SEPARATOR,
        "hover_color": config.COLOR_TEXT_SECONDARY,
        "text_color": config.COLOR_TEXT_PRIMARY,
    },
    # ---- outline / ghost ----
    "ghost": {
        "fg_color": "transparent",
        "hover_color": config.COLOR_ACCENT_HOVER,
        "border_width": 1,
        "border_color": config.COLOR_ACCENT,
    },
    "ghost_subtle": {
        "fg_color": "transparent",
        "hover_color": ("gray80", "gray30"),
        "border_width": 1,
        "border_color": config.COLOR_TEXT_SECONDARY,
        "text_color": config.COLOR_TEXT_SECONDARY,
    },
}


class StyledButton(ctk.CTkButton):
    """
    Single reusable button for every use-case: text, icon-only, or both.

    Parameters
    ----------
    preset : str
        Colour theme name (see _PRESETS).  Default ``"primary"``.
    image_path / hover_image_path / disabled_image_path : str | None
        Paths to icon PNGs.  When *any* image path is given the button
        gains hover-image-swap and enable()/disable() support.
    icon_size : tuple | None
        ``(w, h)`` for the icon.  Defaults to ``config.ICON_SIZE_MEDIUM``.
    round : bool
        If True, ``corner_radius`` is set to ``size // 2`` to make the
        button circular and text is hidden – handy for icon-only buttons.
    size : int | None
        Shortcut that sets both ``width`` and ``height`` to the same value.
        Only meaningful when ``round=True`` (ignored otherwise).
    hover_border_color : str | None
        Border colour while the cursor is over the button.  When set the
        border animates between ``border_color`` and ``hover_border_color``.

    Everything else (``width``, ``height``, ``fg_color``, …) is forwarded
    straight to ``CTkButton``, overriding the preset.

    Usage examples
    --------------
    # plain text button
    StyledButton(parent, text="OK", command=fn)

    # text button with a preset
    StyledButton(parent, text="Delete", preset="danger", command=fn)

    # round icon-only button (replaces old IconButton)
    StyledButton(parent, image_path="start.png", round=True, size=60,
                 preset="success", hover_border_color=COLOR_SUCCESS)

    # text + icon combo
    StyledButton(parent, text="Stop", image_path="stop.png",
                 preset="error", width=120)
    """

    def __init__(
        self,
        master,
        text: str = "",
        preset: str = "primary",
        # ---- image support ----
        image_path: str = None,
        hover_image_path: str = None,
        disabled_image_path: str = None,
        icon_size: tuple = None,
        # ---- shape helpers ----
        round: bool = False,
        size: int = None,
        # ---- visibility ----
        hide_on_disable: bool = False,
        # ---- hover border ----
        hover_border_color: str = None,
        # ---- standard overrides ----
        width: int = None,
        height: int = None,
        corner_radius: int = None,
        font: ctk.CTkFont = None,
        command=None,
        **kwargs,
    ):
        # -- state tracking --
        self._is_enabled = True
        self._hide_on_disable = hide_on_disable
        self._pack_info = None
        self._hover_border = hover_border_color
        self._normal_border = kwargs.get(
            "border_color",
            _PRESETS.get(preset, _PRESETS["primary"]).get("border_color"),
        )

        # -- build merged style dict (preset → kwargs → explicit args) --
        style = dict(_PRESETS.get(preset, _PRESETS["primary"]))
        style.update(kwargs)

        # -- images --
        if icon_size is None:
            icon_size = config.ICON_SIZE_MEDIUM

        self._normal_img = None
        self._hover_img = None
        self._disabled_img = None

        if image_path:
            self._normal_img = self._load_image(image_path, icon_size)
            self._hover_img = (
                self._load_image(hover_image_path, icon_size)
                if hover_image_path
                else self._normal_img
            )
            self._disabled_img = (
                self._load_image(disabled_image_path, icon_size)
                if disabled_image_path
                else self._normal_img
            )
            style["image"] = self._normal_img

        # -- round shortcut --
        if round:
            btn_size = size or config.IMAGE_BUTTON_SIZE
            style.setdefault("width", btn_size)
            style.setdefault("height", btn_size)
            style["corner_radius"] = btn_size // 2
            text = ""  # icon-only
        else:
            if width is not None:
                style["width"] = width
            elif "width" not in style:
                style["width"] = config.BUTTON_WIDTH

            if height is not None:
                style["height"] = height
            elif "height" not in style:
                style["height"] = config.BUTTON_HEIGHT

            if corner_radius is not None:
                style["corner_radius"] = corner_radius
            elif "corner_radius" not in style:
                style["corner_radius"] = config.CORNER_RADIUS_SMALL

        # -- font default --
        if font is not None:
            style["font"] = font
        elif "font" not in style and not round:
            style["font"] = ctk.CTkFont(
                family=config.BUTTON_FONT,
                size=config.BUTTON_FONT_SIZE,
            )

        # -- keep track of normal border after style is finalised --
        if self._normal_border is None:
            self._normal_border = style.get("border_color")

        super().__init__(master, text=text, command=command, **style)

        # -- bind hover events only when there is something to animate --
        if self._hover_border or self._hover_img:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

    # -----------------------------------------------------------------
    # internal helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _load_image(path, size):
        img = Image.open(path)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)

    def _on_enter(self, event=None):
        if not self._is_enabled:
            return
        if self._hover_border:
            self.configure(border_color=self._hover_border)
        if self._hover_img and self._hover_img is not self._normal_img:
            self.configure(image=self._hover_img)

    def _on_leave(self, event=None):
        if not self._is_enabled:
            return
        if self._normal_border:
            self.configure(border_color=self._normal_border)
        if self._normal_img and self._hover_img is not self._normal_img:
            self.configure(image=self._normal_img)

    # -----------------------------------------------------------------
    # public API
    # -----------------------------------------------------------------

    def enable(self):
        self._is_enabled = True
        self.configure(state="normal")
        if self._normal_img:
            self.configure(image=self._normal_img)
        if self._normal_border:
            self.configure(border_color=self._normal_border)
        if self._hide_on_disable and self._pack_info:
            self.pack(**self._pack_info)
            self._pack_info = None

    def disable(self):
        self._is_enabled = False
        self.configure(state="disabled")
        if self._disabled_img:
            self.configure(image=self._disabled_img)
        if self._hide_on_disable:
            try:
                info = self.pack_info()
                self._pack_info = {
                    k: v for k, v in info.items() if k != "in"
                }
            except Exception:
                self._pack_info = None
            self.pack_forget()


# =====================================================================
# Convenience alias so existing imports keep working
# =====================================================================
IconButton = StyledButton
