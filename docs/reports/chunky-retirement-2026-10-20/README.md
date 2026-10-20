# Disposable retirement-interleaving evidence

These are execution receipts for the report, not production tools or a new framework.
The loopback-only Fabric 26.3 fixture uses the unchanged PR #55 controller and
pinned optimization mods. Its fresh worlds are under `/tmp/chunky-retirement-*`.
The driver and client contain the actual machine-local launcher, source and
probe paths used in this run.

Both gated Java sources were compiled with `javac --release 17 -cp /tmp/chunky.jar`
alongside `RetirementGate.java`. The two resulting main classes and gate class
were overlaid onto copies of the original pinned 1.5.3 JAR. The baseline source
has only the test gate inserted before retirement. The patched source adds the
production retirement patch plus the identical test gate. The driver arms a
named FIFO and releases the old worker only after observing selection center
9000 on the registered replacement. No fixed retirement delay is used.

The production build excludes the gate and checks its archive delta separately.

The test client uses the existing staging protocol probe and sends no production
traffic. After join it is placed in spectator mode at replacement center 9000
so its normal activity tracking does not request a second recenter on logout.
The online-pause assertion uses raw unsolicited progress messages; later
`chunky progress` commands are read-only observations to bound the resume check.
