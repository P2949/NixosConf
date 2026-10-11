package local.minecraft.performance;

import com.sun.tools.attach.VirtualMachine;

public final class QueueAttach {
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("pid agent.jar output");
        VirtualMachine machine = VirtualMachine.attach(args[0]);
        try { machine.loadAgent(args[1], args[2]); }
        finally { machine.detach(); }
    }
}
