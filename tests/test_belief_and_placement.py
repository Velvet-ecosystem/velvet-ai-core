import pytest

from velvet_ai_core.belief_and_placement import (
    BeliefState,
    CandidateInterpretation,
    ExecutionPlacement,
    InferenceCostSketch,
    ModelCapability,
    can_commit_belief,
    choose_execution_node,
    useful_work_per_watt_gb,
)


def test_belief_commits_only_with_confidence_and_corroboration():
    belief = BeliefState(
        belief_id="presence-front-room",
        source_observation_ids=("camera-1", "ld2410-1"),
        candidate_interpretations=(
            CandidateInterpretation(label="person_present", confidence=0.91),
            CandidateInterpretation(label="empty_room", confidence=0.09),
        ),
        commit_threshold=0.8,
        requires_corroboration=True,
    )

    assert can_commit_belief(belief) is True


def test_belief_does_not_commit_single_source_when_corroboration_required():
    belief = BeliefState(
        belief_id="presence-front-room",
        source_observation_ids=("camera-1",),
        candidate_interpretations=(CandidateInterpretation(label="person_present", confidence=0.95),),
        commit_threshold=0.8,
        requires_corroboration=True,
    )

    assert can_commit_belief(belief) is False


def test_model_capability_cannot_claim_physical_authority():
    with pytest.raises(ValueError, match="physical authority"):
        ModelCapability(
            capability_name="door-control",
            preferred_provider="local",
            offline_available=True,
            cloud_permission_required=False,
            max_authority_level="command",
        ).validate()


def test_execution_placement_does_not_change_authority():
    placement = ExecutionPlacement(
        capability_name="vision-local",
        execution_location_policy="local-preferred",
        allowed_nodes=("queen-up2", "vision-node"),
        forbidden_nodes=("cloud",),
        data_may_leave_origin_node=False,
        max_latency_ms=50,
        authority_changes_if_moved=False,
    )

    assert choose_execution_node(placement, ("vision-node",)) == "vision-node"


def test_execution_placement_rejects_authority_change():
    with pytest.raises(ValueError, match="cannot change authority"):
        ExecutionPlacement(
            capability_name="vision-local",
            execution_location_policy="movable",
            allowed_nodes=("queen-up2",),
            authority_changes_if_moved=True,
        ).validate()


def test_execution_placement_returns_none_when_no_healthy_allowed_node_exists():
    placement = ExecutionPlacement(
        capability_name="vision-local",
        execution_location_policy="local-preferred",
        allowed_nodes=("queen-up2",),
        forbidden_nodes=(),
    )

    assert choose_execution_node(placement, ("velour",)) is None


def test_inference_cost_sketch_validates_processor_and_costs():
    sketch = InferenceCostSketch(
        capability_requested="reasoning-small",
        model_name_or_local_id="local-small-v1",
        execution_location="queen-up2",
        processor_class="cpu",
        runtime_ms=120,
        memory_peak_mb=512,
        estimated_energy_j=2.5,
    )

    sketch.validate()


def test_useful_work_per_watt_gb_scores_validated_workload():
    score = useful_work_per_watt_gb(throughput=20.0, watts=10.0, memory_mb=2048)

    assert score == 1.0


def test_useful_work_per_watt_gb_rejects_zero_watts():
    with pytest.raises(ValueError, match="watts"):
        useful_work_per_watt_gb(throughput=20.0, watts=0.0, memory_mb=2048)
