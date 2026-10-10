# Historical closure comparisons

Point-in-time qualification evidence; see the [canonical baseline](../baseline-final.md).

## Root-policy preparation, 2026-10-05

Compared the running third-trial closure
`/nix/store/jj4h7abqachf769dpz308v480a6srdbs-nixos-system-desktop-26.05.20261002.774debe`
with the built default/recovery candidate
`/nix/store/j4mmsn2b0bhblr06jhx4jnp7s4qp1w9p-nixos-system-desktop-26.05.20261002.774debe`.

The comparison reported size changes in generated `dbus`, `etc`, `initrd-linux`,
configuration reference/manual, `nixos-system-desktop`, `system` and `user`
outputs. It reported no package version transitions. The candidate includes
the additional persistent-root recovery closure. No activation or host reboot
was performed by this review.

## Readiness guards candidate review, 2026-10-05

Accepted normal closure `czk5a2wn8di3pgv8a6w0b8aj3286g3h3` was compared with
uninstalled candidate `l994fn5hpd2g2rijyffprl4368587m5w`; both are
`nixos-system-desktop-26.05.20261004.0d9e9b8`. Current source dc668d0 still
evaluates to that exact candidate. Persistent counterpart is
`cxc50rmb8i6akb62fcvzz3xkszzqf895`.

Closure sizes: 16,985,654,488 → 16,985,659,544 bytes (+5,056). No package-version
transitions are reported. Membership: 2,207 → 2,208 paths, with12 added/11
removed. All changes are generated etc/system units, Commander keeper source
and wrapper/unit, initrd, normal/persistent system outputs, pre-switch checks
and the new workstation activation checker. Kernel store path is identical
(`na8n3qdqf1fs7lwads81ra9nlh1hqc9w-linux-6.18.55`).

Material explanations: explicit Bash reset data interface changes initrd;
required Commander policy arguments and derived watchdog change keeper/unit;
named read-only activation prerequisites change pre-switch checker and switch
references. Top-level activate/prepare-root/boot metadata references follow the
new system identities. No compiler optimization or dependency refresh occurred.
The forbidden stock namespaces and build checks are build-time protections.

Private closure membership and recursive system-output differences are retained
under `/persist/nixos-readiness-20261005`. This is preparation review, not
physical acceptance or the final freeze comparison. Both old and candidate
closures remain GC-protected; no installation or profile replacement occurred.
