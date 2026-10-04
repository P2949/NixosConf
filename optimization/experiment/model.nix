{ lib }:

let
  fail = message: throw "optimization experiment schema: ${message}";

  require = condition: message: if condition then true else fail message;

  nonEmptyString = value: builtins.isString value && value != "";

  all = predicate: values: builtins.all predicate values;

  uniqueIds =
    values:
    let
      ids = map (value: value.id) values;
    in
    builtins.length ids == builtins.length (lib.unique ids);

  allowedStageKinds = [
    "cpu-codegen"
    "compiler-tuning"
    "lto"
    "pgo"
    "bolt"
    "combined"
  ];

  allowedTargetKinds = [
    "system"
    "package"
  ];

  allowedMetricDirections = [
    "lower-is-better"
    "higher-is-better"
  ];

  normalizeMetric =
    metric:

    let
      id = metric.id or "";
      unit = metric.unit or "";
      direction = metric.direction or "";
    in
    assert require (builtins.isAttrs metric) "metric must be an attribute set";
    assert require (nonEmptyString id) "metric.id must be a non-empty string";
    assert require (nonEmptyString unit) "metric.unit must be a non-empty string";
    assert require (lib.elem direction allowedMetricDirections)
      "metric.direction must be lower-is-better or higher-is-better";
    {
      inherit id unit direction;
    };

  normalizeWorkload =
    workload:

    let
      id = workload.id or "";
      description = workload.description or "";
      command = workload.command or [ ];
      metrics = workload.metrics or [ ];
      warmupRuns = workload.warmupRuns or 2;
      measurementRuns = workload.measurementRuns or 10;

      normalizedMetrics = map normalizeMetric metrics;
    in
    assert require (builtins.isAttrs workload) "workload must be an attribute set";
    assert require (nonEmptyString id) "workload.id must be a non-empty string";
    assert require (nonEmptyString description) "workload.description must be a non-empty string";
    assert require (
      builtins.isList command && command != [ ] && all nonEmptyString command
    ) "workload.command must be a non-empty argv list";
    assert require (
      builtins.isList metrics && metrics != [ ]
    ) "workload.metrics must be a non-empty list";
    assert require (uniqueIds normalizedMetrics) "metric IDs must be unique within each workload";
    assert require (
      builtins.isInt warmupRuns && warmupRuns >= 0
    ) "workload.warmupRuns must be a non-negative integer";
    assert require (
      builtins.isInt measurementRuns && measurementRuns > 0
    ) "workload.measurementRuns must be a positive integer";
    {
      inherit
        id
        description
        command
        warmupRuns
        measurementRuns
        ;

      metrics = normalizedMetrics;
    };

  normalizeTarget =
    target:

    let
      id = target.id or "";
      kind = target.kind or "";
      attribute = target.attribute or "";
    in
    assert require (builtins.isAttrs target) "target must be an attribute set";
    assert require (nonEmptyString id) "target.id must be a non-empty string";
    assert require (lib.elem kind allowedTargetKinds) "target.kind must be system or package";
    assert require (nonEmptyString attribute) "target.attribute must be a non-empty flake attribute";
    {
      inherit id kind attribute;
    };

  normalizeStage =
    stage:

    let
      kind = stage.kind or "";
      parameters = stage.parameters or { };
    in
    assert require (builtins.isAttrs stage) "stage must be an attribute set";
    assert require (lib.elem kind allowedStageKinds) "unsupported optimization stage kind: ${kind}";
    assert require (builtins.isAttrs parameters) "stage.parameters must be an attribute set";
    {
      inherit kind parameters;
    };

  normalizeSpec =
    spec:

    let
      id = spec.id or "";
      hypothesis = spec.hypothesis or "";
      targets = spec.targets or [ ];
      workloads = spec.workloads or [ ];

      normalizedTargets = map normalizeTarget targets;
      normalizedWorkloads = map normalizeWorkload workloads;
    in
    assert require (builtins.isAttrs spec) "experiment spec must be an attribute set";
    assert require (nonEmptyString id) "experiment id must be a non-empty string";
    assert require (nonEmptyString hypothesis) "experiment hypothesis must be a non-empty string";
    assert require (
      builtins.isList targets && targets != [ ]
    ) "experiment must define at least one target";
    assert require (uniqueIds normalizedTargets) "target IDs must be unique";
    assert require (
      builtins.isList workloads && workloads != [ ]
    ) "experiment must define at least one workload";
    assert require (uniqueIds normalizedWorkloads) "workload IDs must be unique";
    {
      schemaVersion = 1;
      kind = "nixos-optimization-experiment-spec";

      inherit id hypothesis;

      stage = normalizeStage spec.stage;

      targets = normalizedTargets;
      workloads = normalizedWorkloads;
    };
in
{
  inherit
    allowedMetricDirections
    allowedStageKinds
    allowedTargetKinds
    normalizeSpec
    ;
}
