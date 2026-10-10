{ lib }:
let
  fail = message: throw "experiment schema: ${message}";
  require = condition: message: if condition then true else fail message;
  text = value: builtins.isString value && value != "";
  closed =
    fields: value:
    builtins.isAttrs value && builtins.attrNames value == lib.sort builtins.lessThan fields;
  unique =
    values: builtins.length values == builtins.length (lib.unique (map (value: value.id) values));
  metric =
    value:
    assert require (closed [ "id" "unit" "direction" ] value) "invalid metric fields";
    assert require (
      text value.id
      && text value.unit
      && lib.elem value.direction [
        "higher-is-better"
        "lower-is-better"
      ]
    ) "invalid metric";
    value;
  sampling =
    value:
    assert require (closed [
      "pilotPairs"
      "minimumPairs"
      "maximumPairs"
      "targetDeltaHalfWidth"
      "effectThreshold"
      "orderSeed"
    ] value) "invalid sampling fields";
    assert require (
      builtins.isInt value.pilotPairs && value.pilotPairs >= 2
    ) "pilot requires at least two pairs";
    assert require (
      builtins.isInt value.minimumPairs
      && builtins.isInt value.maximumPairs
      && value.minimumPairs >= 2
      && value.maximumPairs >= value.minimumPairs
    ) "invalid pair bounds";
    assert require (
      builtins.isFloat value.targetDeltaHalfWidth
      && value.targetDeltaHalfWidth > 0
      && value.targetDeltaHalfWidth < 1
    ) "invalid relative precision";
    assert require (
      builtins.isFloat value.effectThreshold && value.effectThreshold >= 0 && value.effectThreshold < 1
    ) "invalid effect threshold";
    assert require (builtins.isInt value.orderSeed && value.orderSeed >= 0) "invalid order seed";
    value;
  workload =
    value:
    assert require (closed [
      "id"
      "description"
      "executable"
      "arguments"
      "metrics"
      "warmupRuns"
      "minimumSeconds"
      "sampling"
      "corpusId"
      "cpu"
    ] value) "invalid workload fields";
    assert require (builtins.isInt value.cpu && value.cpu >= 0) "invalid pinned CPU";
    assert require (
      text value.id && text value.description && text value.corpusId
    ) "invalid workload identity";
    assert require (
      text value.executable && builtins.isList value.arguments && builtins.all text value.arguments
    ) "executable and argument list required";
    assert require (
      builtins.isInt value.warmupRuns
      && value.warmupRuns >= 0
      && builtins.isInt value.minimumSeconds
      && value.minimumSeconds > 0
    ) "invalid warmup/duration";
    assert require (builtins.isList value.metrics && value.metrics != [ ]) "metrics required";
    let
      metrics = map metric value.metrics;
    in
    assert require (unique metrics) "duplicate metric IDs";
    value
    // {
      inherit metrics;
      sampling = sampling value.sampling;
    };
  target =
    value:
    assert require (closed [ "id" "kind" "attribute" ] value) "invalid target fields";
    assert require (
      text value.id
      && text value.attribute
      && lib.elem value.kind [
        "package"
        "system"
      ]
    ) "invalid target identity";
    value;
  stage =
    value:
    assert require (closed [ "kind" "parameters" ] value) "invalid stage fields";
    assert require (lib.elem value.kind [
      "stock"
      "cpu-codegen"
    ]) "stage implementation not yet supported";
    assert require (
      if value.kind == "stock" then
        value.parameters == { }
      else
        closed [ "march" "mtune" "packageAllowList" ] value.parameters
        && text value.parameters.march
        && text value.parameters.mtune
        && builtins.isList value.parameters.packageAllowList
        && value.parameters.packageAllowList != [ ]
        && builtins.all text value.parameters.packageAllowList
    ) "invalid stage parameters/allow-list";
    value;
  normalize =
    value:
    assert require (closed [
      "schemaVersion"
      "id"
      "hypothesis"
      "stage"
      "targets"
      "workloads"
      "physicalTarget"
    ] value) "invalid experiment fields";
    assert require (
      value.schemaVersion == 2 && text value.id && text value.hypothesis
    ) "invalid experiment identity/version";
    assert require (
      closed [ "hostname" "cpuVendor" "cpuFamily" "cpuModel" ] value.physicalTarget
      && builtins.all text (builtins.attrValues value.physicalTarget)
    ) "invalid physical target";
    assert require (
      builtins.isList value.targets
      && value.targets != [ ]
      && builtins.isList value.workloads
      && value.workloads != [ ]
    ) "targets and workloads required";
    let
      targets = map target value.targets;
      workloads = map workload value.workloads;
    in
    assert require (unique targets && unique workloads) "duplicate target/workload IDs";
    value
    // {
      inherit targets workloads;
      stage = stage value.stage;
      kind = "nixos-optimization-experiment-spec";
    };
in
{
  normalizeSpec =
    value:
    let
      result = normalize value;
    in
    builtins.deepSeq result result;
}
