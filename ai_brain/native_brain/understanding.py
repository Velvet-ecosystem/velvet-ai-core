"""Contextual interpretation stage for the Native Brain."""

from .models import BrainContext, Observation, Understanding


class Understander:
    """Place an observation inside its current working context."""

    def understand(
        self, observation: Observation, context: BrainContext
    ) -> Understanding:
        summary = (
            f"{observation.event_type} from {observation.source} "
            f"while runtime_mode={context.runtime_mode} "
            f"and presence={context.presence}"
        )
        return Understanding(
            observation=observation,
            context=context,
            summary=summary,
        )
