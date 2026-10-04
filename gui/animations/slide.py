"""
Slide Animations — Smooth entrance/exit transitions from any direction.
"""
from gui.animations.engine import AnimationController, Easing

class SlideAnimations:
    """Slide widgets in from off-screen positions."""

    @staticmethod
    def slide_in_from_left(widget, target_x, start_x=-300, duration_ms=500, on_complete=None):
        """Slide a widget from left off-screen to its target position."""
        widget.place_configure(x=start_x)
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            current_x = int(start_x + (target_x - start_x) * progress)
            widget.place_configure(x=current_x)

        controller.animate(update, Easing.ease_out_cubic, on_complete)

    @staticmethod
    def slide_in_from_right(widget, target_x, start_x=1200, duration_ms=500, on_complete=None):
        """Slide a widget from right off-screen to its target position."""
        widget.place_configure(x=start_x)
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            current_x = int(start_x + (target_x - start_x) * progress)
            widget.place_configure(x=current_x)

        controller.animate(update, Easing.ease_out_cubic, on_complete)

    @staticmethod
    def slide_in_from_bottom(widget, target_y, start_y=800, duration_ms=500, on_complete=None):
        """Slide a widget up from below the window."""
        widget.place_configure(y=start_y)
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            current_y = int(start_y + (target_y - start_y) * progress)
            widget.place_configure(y=current_y)

        controller.animate(update, Easing.ease_out_back, on_complete)

    @staticmethod
    def slide_in_from_top(widget, target_y, start_y=-200, duration_ms=500, on_complete=None):
        """Slide a widget down from above the window."""
        widget.place_configure(y=start_y)
        controller = AnimationController(widget, duration_ms)

        def update(progress):
            current_y = int(start_y + (target_y - start_y) * progress)
            widget.place_configure(y=current_y)

        controller.animate(update, Easing.ease_out_cubic, on_complete)

    @staticmethod
    def slide_cards_staggered(parent, cards: list, start_x=-400, target_x=0, 
                                stagger_ms=80, duration_ms=450):
        """Slide multiple cards in with a staggered delay — cascading entrance."""
        for i, card in enumerate(cards):
            delay = i * stagger_ms

            def create_slide(c, d):
                def do_slide():
                    SlideAnimations.slide_in_from_left(c, target_x, start_x, duration_ms)
                parent.after(d, do_slide)

            create_slide(card, delay)