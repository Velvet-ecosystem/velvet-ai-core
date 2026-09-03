# SPDX-License-Identifier: GPL-3.0-only

from velvet.core.native_brain.body_capacity import (
    ResourceAdvertisement,
    ResourceAwareDistributedBodyPlanner,
    ResourceKind,
    ResourceRequirement,
    ResourceScope,
    NodeResourceAdvertisement,
    build_body_capacity_snapshot,
)
from velvet.core.native_brain.distributed_body import (
    NodeAdvertisement,
    NodeAvailability,
    NodeTier,
    PlacementDisposition,
    WorkRequirement,
)


def node(node_id, organ, tier, capability, load=0.2):
    return NodeAdvertisement(
        node_id=node_id,
        organ=organ,
        tier=tier,
        capabilities=(capability,),
        current_load=load,
        health=0.95,
        availability=NodeAvailability.AVAILABLE,
    )


def resources(node_id, *items, observed_at=1.0):
    return NodeResourceAdvertisement(
        node_id=node_id,
        body_id="velvet-body",
        observed_at=observed_at,
        resources=tuple(items),
    )


def storage(resource_id, available, *, scope=ResourceScope.ATTACHED):
    return ResourceAdvertisement(
        resource_id=resource_id,
        kind=ResourceKind.STORAGE,
        scope=scope,
        capacity=1_000_000_000_000,
        available=available,
        unit="bytes",
        capabilities=("library.archive",),
    )


def memory(resource_id, capacity, available):
    return ResourceAdvertisement(
        resource_id=resource_id,
        kind=ResourceKind.MEMORY,
        scope=ResourceScope.LOCAL,
        capacity=capacity,
        available=available,
        unit="bytes",
    )


def work():
    return WorkRequirement(
        work_id="work.library.index",
        work_class="library.indexing",
        required_capabilities=("library.index",),
    )


def test_body_snapshot_counts_attached_storage_where_it_is_hosted():
    founder = resources(
        "founder",
        memory("ram", 8_000_000_000, 4_000_000_000),
        storage("usb-1tb", 800_000_000_000),
    )

    snapshot = build_body_capacity_snapshot((founder,))

    storage_total = next(item for item in snapshot.totals if item.kind is ResourceKind.STORAGE)
    assert storage_total.capacity == 1_000_000_000_000
    assert storage_total.available == 800_000_000_000
    assert snapshot.node_ids == ("founder",)
    assert snapshot.authority == "none"


def test_moving_same_storage_to_velour_changes_host_not_body_capacity():
    founder_first = resources("founder", storage("library-disk", 700_000_000_000))
    velour_later = resources("velour", storage("library-disk", 700_000_000_000), observed_at=2.0)

    founder_snapshot = build_body_capacity_snapshot((founder_first,))
    velour_snapshot = build_body_capacity_snapshot((velour_later,))

    founder_storage = next(item for item in founder_snapshot.totals if item.kind is ResourceKind.STORAGE)
    velour_storage = next(item for item in velour_snapshot.totals if item.kind is ResourceKind.STORAGE)
    assert founder_storage.available == velour_storage.available
    assert founder_snapshot.node_ids == ("founder",)
    assert velour_snapshot.node_ids == ("velour",)


def test_resource_gate_prefers_host_that_actually_has_required_ram():
    founder = node("founder", "queen", NodeTier.QUEEN, "library.index", load=0.1)
    lyra = node("velour", "librarian", NodeTier.SPECIALIST_LINUX, "library.index", load=0.3)
    advertisements = (
        resources("founder", memory("ram", 8_000_000_000, 700_000_000)),
        resources("velour", memory("ram", 4_000_000_000, 2_000_000_000)),
    )
    requirement = ResourceRequirement(
        kind=ResourceKind.MEMORY,
        minimum_available=1_000_000_000,
        unit="bytes",
    )

    result = ResourceAwareDistributedBodyPlanner().propose(
        work(),
        (founder, lyra),
        resource_advertisements=advertisements,
        resource_requirements=(requirement,),
    )

    assert result.disposition is PlacementDisposition.PLACE_CANDIDATE
    assert result.candidates[0].node_id == "velour"
    assert any("founder:resource-requirement-unmet" == reason for reason in result.reasons)


def test_attached_storage_can_make_founder_eligible_without_board_specific_rule():
    founder = node("founder", "queen", NodeTier.QUEEN, "library.index", load=0.1)
    requirement = ResourceRequirement(
        kind=ResourceKind.STORAGE,
        minimum_available=500_000_000_000,
        unit="bytes",
        required_capabilities=("library.archive",),
    )

    without_drive = ResourceAwareDistributedBodyPlanner().propose(
        work(),
        (founder,),
        resource_advertisements=(resources("founder", memory("ram", 8_000_000_000, 4_000_000_000)),),
        resource_requirements=(requirement,),
    )
    with_drive = ResourceAwareDistributedBodyPlanner().propose(
        work(),
        (founder,),
        resource_advertisements=(resources("founder", storage("usb-1tb", 800_000_000_000)),),
        resource_requirements=(requirement,),
    )

    assert without_drive.disposition is PlacementDisposition.UNAVAILABLE
    assert with_drive.disposition is PlacementDisposition.PLACE_CANDIDATE
    assert with_drive.candidates[0].node_id == "founder"


def test_resource_free_work_uses_existing_planner_unchanged():
    founder = node("founder", "queen", NodeTier.QUEEN, "library.index", load=0.1)
    lyra = node("velour", "librarian", NodeTier.SPECIALIST_LINUX, "library.index", load=0.3)
    planner = ResourceAwareDistributedBodyPlanner()

    delegated = planner.propose(work(), (founder, lyra))

    assert delegated.candidates[0].node_id == "velour"


def test_unverified_resource_advertisement_cannot_make_node_eligible():
    founder = node("founder", "queen", NodeTier.QUEEN, "library.index")
    bad = NodeResourceAdvertisement(
        node_id="founder",
        body_id="wrong-or-unverified",
        observed_at=1.0,
        resources=(storage("usb-1tb", 800_000_000_000),),
        body_verified=False,
    )
    requirement = ResourceRequirement(
        kind=ResourceKind.STORAGE,
        minimum_available=1.0,
        unit="bytes",
    )

    result = ResourceAwareDistributedBodyPlanner().propose(
        work(),
        (founder,),
        resource_advertisements=(bad,),
        resource_requirements=(requirement,),
    )

    assert result.disposition is PlacementDisposition.UNAVAILABLE
