import type { ProjectState } from "../types/project";

export const mockProject: ProjectState = {
  id: "project-1",
  name: "24V Presence Sensor",
  phase: "draft",
  requirements: [
    { id: "r1", text: "24V DC input" },
    { id: "r2", text: "ESP32-C3 as controller" },
    { id: "r3", text: "mmWave presence detection" },
    { id: "r4", text: "Temperature and humidity sensor" },
    { id: "r5", text: "Relay output" },
  ],
  blocks: [
    {
      id: "b1",
      name: "24V Input Protection",
      description: "Reverse polarity, optional TVS, bulk capacitor",
      status: "draft",
    },
    {
      id: "b2",
      name: "Buck 24V to 5V",
      description: "Primary DC/DC stage",
      status: "draft",
    },
    {
      id: "b3",
      name: "LDO 5V to 3.3V",
      description: "Clean supply for MCU and sensor domain",
      status: "draft",
    },
    {
      id: "b4",
      name: "ESP32-C3 Core",
      description: "MCU module with UART access",
      status: "draft",
    },
    {
      id: "b5",
      name: "Relay Driver",
      description: "Low-side transistor stage with flyback path",
      status: "draft",
    },
  ],
  components: [
    {
      id: "c1",
      ref: "U1",
      name: "ESP32-C3-WROOM-02",
      category: "MCU Module",
      trustLevel: "trusted_template",
    },
    {
      id: "c2",
      ref: "U2",
      name: "AP7333-33",
      category: "LDO",
      trustLevel: "validated",
    },
    {
      id: "c3",
      ref: "U3",
      name: "SHT31",
      category: "Sensor",
      trustLevel: "validated",
    },
    {
      id: "c4",
      ref: "U4",
      name: "LD2410 Variant",
      category: "mmWave Module",
      trustLevel: "parsed",
    },
  ],
  validationIssues: [
    {
      id: "v1",
      title: "mmWave module not fully validated",
      description: "Pinout and supply assumptions still need review.",
      severity: "warning",
    },
    {
      id: "v2",
      title: "Relay coil current not confirmed",
      description: "Driver transistor sizing depends on selected relay.",
      severity: "warning",
    },
    {
      id: "v3",
      title: "I2C pull-ups missing in draft",
      description: "Check whether they are already present on the sensor board.",
      severity: "info",
    },
  ],
  chatMessages: [
    {
      id: "m1",
      role: "user",
      content: "I need a 24V presence sensor with ESP32-C3, mmWave, SHT31 and relay output.",
    },
    {
      id: "m2",
      role: "assistant",
      content:
        "Proposed architecture: 24V input protection, buck to 5V, LDO to 3.3V, ESP32-C3 core, mmWave module, SHT31 and low-side relay driver.",
    },
  ],
};