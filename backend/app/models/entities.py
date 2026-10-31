from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Plant(Base):
    __tablename__ = "plants"

    plant_id = Column(String(64), primary_key=True)
    plant_code = Column(String(32), unique=True, nullable=False)
    plant_name = Column(String(128), nullable=False)
    location = Column(String(256), nullable=False)
    timezone = Column(String(64), nullable=False, default="UTC")
    status = Column(String(32), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    machines = relationship("Machine", back_populates="plant", cascade="all, delete-orphan")
    safety_zones = relationship("SafetyZone", back_populates="plant", cascade="all, delete-orphan")
    shifts = relationship("OperatorShift", back_populates="plant")
    incidents = relationship("Incident", back_populates="plant")


class Machine(Base):
    __tablename__ = "machines"

    machine_id = Column(String(64), primary_key=True)
    plant_id = Column(String(64), ForeignKey("plants.plant_id", ondelete="RESTRICT"), nullable=False)
    machine_code = Column(String(32), unique=True, nullable=False)
    machine_name = Column(String(128), nullable=False)
    machine_type = Column(String(64), nullable=False)
    operational_status = Column(String(32), nullable=False, default="IDLE")
    commissioned_at = Column(DateTime, nullable=False)
    retired_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    plant = relationship("Plant", back_populates="machines")
    interlocks = relationship("Interlock", back_populates="machine", cascade="all, delete-orphan")
    alarm_events = relationship("AlarmEvent", back_populates="machine")
    state_histories = relationship("MachineStateHistory", back_populates="machine", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="machine")
    safety_zone_mappings = relationship("MachineSafetyZone", back_populates="machine", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_machines_plant", "plant_id"),
        Index("idx_machines_status", "operational_status"),
    )


class SafetyZone(Base):
    __tablename__ = "safety_zones"

    safety_zone_id = Column(String(64), primary_key=True)
    plant_id = Column(String(64), ForeignKey("plants.plant_id", ondelete="RESTRICT"), nullable=False)
    zone_code = Column(String(32), nullable=False)
    zone_name = Column(String(128), nullable=False)
    risk_level = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE")

    # Relationships
    plant = relationship("Plant", back_populates="safety_zones")
    alarm_events = relationship("AlarmEvent", back_populates="safety_zone")
    machine_mappings = relationship("MachineSafetyZone", back_populates="safety_zone", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="safety_zone")

    __table_args__ = (
        Index("idx_safety_zones_plant", "plant_id"),
    )


class MachineSafetyZone(Base):
    __tablename__ = "machine_safety_zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String(64), ForeignKey("machines.machine_id", ondelete="CASCADE"), nullable=False)
    safety_zone_id = Column(String(64), ForeignKey("safety_zones.safety_zone_id", ondelete="RESTRICT"), nullable=False)
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    machine = relationship("Machine", back_populates="safety_zone_mappings")
    safety_zone = relationship("SafetyZone", back_populates="machine_mappings")

    __table_args__ = (
        Index("idx_msz_machine_zone", "machine_id", "safety_zone_id"),
    )


class Interlock(Base):
    __tablename__ = "interlocks"

    interlock_id = Column(String(64), primary_key=True)
    machine_id = Column(String(64), ForeignKey("machines.machine_id", ondelete="CASCADE"), nullable=False)
    interlock_code = Column(String(32), nullable=False)
    interlock_name = Column(String(128), nullable=False)
    interlock_type = Column(String(64), nullable=False)
    expected_safe_state = Column(String(32), nullable=False)
    current_state = Column(String(32), nullable=False)
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE")

    # Relationships
    machine = relationship("Machine", back_populates="interlocks")
    state_histories = relationship("InterlockStateHistory", back_populates="interlock", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_interlocks_machine", "machine_id"),
    )


class AlarmDefinition(Base):
    __tablename__ = "alarm_definitions"

    alarm_definition_id = Column(String(64), primary_key=True)
    alarm_code = Column(String(32), unique=True, nullable=False)
    machine_type = Column(String(64), nullable=False)
    alarm_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(16), nullable=False)  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    acknowledgement_required = Column(Boolean, nullable=False, default=True)
    acknowledgement_sla_seconds = Column(Integer, nullable=False, default=300)
    expected_interlock_state = Column(String(32), nullable=True)
    active_from = Column(DateTime, nullable=False)
    active_to = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, default="ACTIVE")

    # Relationships
    alarm_events = relationship("AlarmEvent", back_populates="alarm_definition")

    __table_args__ = (
        Index("idx_alarm_def_severity", "severity"),
        Index("idx_alarm_def_machine_type", "machine_type"),
    )


class OperatorShift(Base):
    __tablename__ = "operator_shifts"

    shift_id = Column(String(64), primary_key=True)
    operator_code = Column(String(32), nullable=False)
    shift_name = Column(String(64), nullable=False)
    plant_id = Column(String(64), ForeignKey("plants.plant_id", ondelete="RESTRICT"), nullable=False)
    shift_start = Column(DateTime, nullable=False)
    shift_end = Column(DateTime, nullable=False)
    status = Column(String(32), nullable=False, default="COMPLETED")

    # Relationships
    plant = relationship("Plant", back_populates="shifts")
    acknowledgements = relationship("Acknowledgement", back_populates="shift")

    __table_args__ = (
        Index("idx_shifts_plant_time", "plant_id", "shift_start", "shift_end"),
    )


class AlarmEvent(Base):
    __tablename__ = "alarm_events"

    alarm_event_id = Column(String(64), primary_key=True)  # ALM-<machine-id>-000001
    machine_id = Column(String(64), ForeignKey("machines.machine_id", ondelete="RESTRICT"), nullable=False)
    alarm_definition_id = Column(String(64), ForeignKey("alarm_definitions.alarm_definition_id", ondelete="RESTRICT"), nullable=False)
    safety_zone_id = Column(String(64), ForeignKey("safety_zones.safety_zone_id", ondelete="SET NULL"), nullable=True)
    event_timestamp = Column(DateTime, nullable=False)
    received_timestamp = Column(DateTime, nullable=False)
    event_sequence = Column(Integer, nullable=False)
    machine_state = Column(String(32), nullable=False)
    interlock_state_snapshot = Column(String(64), nullable=False)
    alarm_status = Column(String(32), nullable=False, default="ACTIVE")
    source_event_id = Column(String(64), nullable=False)
    replay_reference = Column(String(64), nullable=True)
    issue_type = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    machine = relationship("Machine", back_populates="alarm_events")
    alarm_definition = relationship("AlarmDefinition", back_populates="alarm_events")
    safety_zone = relationship("SafetyZone", back_populates="alarm_events")
    acknowledgements = relationship("Acknowledgement", back_populates="alarm_event", cascade="all, delete-orphan")
    triggered_incidents = relationship("Incident", back_populates="triggering_alarm_event")

    __table_args__ = (
        Index("idx_alarm_events_timestamp", "event_timestamp"),
        Index("idx_alarm_events_machine_time", "machine_id", "event_timestamp"),
        Index("idx_alarm_events_def", "alarm_definition_id"),
        Index("idx_alarm_events_source", "source_event_id"),
        Index("idx_alarm_events_status", "alarm_status"),
    )


class Acknowledgement(Base):
    __tablename__ = "acknowledgements"

    acknowledgement_id = Column(String(64), primary_key=True)  # ACK-<alarm-id>-01
    alarm_event_id = Column(String(64), ForeignKey("alarm_events.alarm_event_id", ondelete="RESTRICT"), nullable=False)
    shift_id = Column(String(64), ForeignKey("operator_shifts.shift_id", ondelete="SET NULL"), nullable=True)
    acknowledgement_timestamp = Column(DateTime, nullable=False)
    acknowledgement_status = Column(String(32), nullable=False, default="TIMELY")
    response_seconds = Column(Integer, nullable=False)
    acknowledgement_channel = Column(String(32), nullable=False, default="HMI_TOUCHPANEL")
    notes = Column(Text, nullable=True)
    issue_type = Column(String(64), nullable=True)

    # Relationships
    alarm_event = relationship("AlarmEvent", back_populates="acknowledgements")
    shift = relationship("OperatorShift", back_populates="acknowledgements")

    __table_args__ = (
        Index("idx_ack_alarm_event", "alarm_event_id"),
        Index("idx_ack_timestamp", "acknowledgement_timestamp"),
        Index("idx_ack_status", "acknowledgement_status"),
    )


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(64), primary_key=True)  # INC-2026-000001
    plant_id = Column(String(64), ForeignKey("plants.plant_id", ondelete="RESTRICT"), nullable=False)
    machine_id = Column(String(64), ForeignKey("machines.machine_id", ondelete="RESTRICT"), nullable=False)
    safety_zone_id = Column(String(64), ForeignKey("safety_zones.safety_zone_id", ondelete="RESTRICT"), nullable=False)
    incident_timestamp = Column(DateTime, nullable=False)
    incident_type = Column(String(64), nullable=False)
    severity = Column(String(16), nullable=False)
    description = Column(Text, nullable=False)
    triggering_alarm_event_id = Column(String(64), ForeignKey("alarm_events.alarm_event_id", ondelete="SET NULL"), nullable=True)
    detection_rule_id = Column(String(64), nullable=False)
    incident_status = Column(String(32), nullable=False, default="OPEN")
    ground_truth_label = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    plant = relationship("Plant", back_populates="incidents")
    machine = relationship("Machine", back_populates="incidents")
    safety_zone = relationship("SafetyZone", back_populates="incidents")
    triggering_alarm_event = relationship("AlarmEvent", back_populates="triggered_incidents")
    corrective_actions = relationship("CorrectiveAction", back_populates="incident", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_incidents_timestamp", "incident_timestamp"),
        Index("idx_incidents_machine_plant", "machine_id", "plant_id"),
        Index("idx_incidents_status", "incident_status"),
    )


class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"

    corrective_action_id = Column(String(64), primary_key=True)  # ACT-<incident-id>-01
    incident_id = Column(String(64), ForeignKey("incidents.incident_id", ondelete="RESTRICT"), nullable=False)
    action_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    assigned_team = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_status = Column(String(32), nullable=False, default="PENDING")
    action_status = Column(String(32), nullable=False, default="OPEN")
    issue_type = Column(String(64), nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="corrective_actions")

    __table_args__ = (
        Index("idx_corrective_action_incident", "incident_id"),
        Index("idx_corrective_action_status", "action_status", "verification_status"),
    )


class MachineStateHistory(Base):
    __tablename__ = "machine_state_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String(64), ForeignKey("machines.machine_id", ondelete="CASCADE"), nullable=False)
    state = Column(String(32), nullable=False)
    transition_timestamp = Column(DateTime, nullable=False)
    trigger_source = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    machine = relationship("Machine", back_populates="state_histories")

    __table_args__ = (
        Index("idx_msh_machine_time", "machine_id", "transition_timestamp"),
    )


class InterlockStateHistory(Base):
    __tablename__ = "interlock_state_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    interlock_id = Column(String(64), ForeignKey("interlocks.interlock_id", ondelete="CASCADE"), nullable=False)
    state = Column(String(32), nullable=False)
    transition_timestamp = Column(DateTime, nullable=False)
    trigger_event_id = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    interlock = relationship("Interlock", back_populates="state_histories")

    __table_args__ = (
        Index("idx_ish_interlock_time", "interlock_id", "transition_timestamp"),
    )


class AlarmReplayGroup(Base):
    __tablename__ = "alarm_replay_groups"

    group_id = Column(String(64), primary_key=True)
    original_event_id = Column(String(64), ForeignKey("alarm_events.alarm_event_id", ondelete="CASCADE"), nullable=False)
    replay_event_id = Column(String(64), ForeignKey("alarm_events.alarm_event_id", ondelete="CASCADE"), nullable=False)
    time_delta_seconds = Column(Float, nullable=False)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_arg_original", "original_event_id"),
        Index("idx_arg_replay", "replay_event_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    action = Column(String(32), nullable=False)
    actor = Column(String(64), nullable=False)
    changes_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_timestamp", "timestamp"),
    )


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    rule_id = Column(String(64), primary_key=True)  # RULE-001, etc.
    rule_name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    threshold_config_json = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DataGenerationRun(Base):
    __tablename__ = "data_generation_runs"

    run_id = Column(String(64), primary_key=True)
    seed = Column(Integer, nullable=False)
    profile = Column(String(32), nullable=False)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    manifest_json = Column(Text, nullable=False)
    canonical_checksum = Column(String(64), nullable=False)
