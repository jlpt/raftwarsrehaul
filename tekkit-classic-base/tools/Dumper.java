package dumper;

import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import org.bukkit.Bukkit;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.craftbukkit.CraftWorld;
import net.minecraft.server.*;

public class Dumper extends JavaPlugin {
    File dir;

    public void onEnable() {
        dir = new File("plugins/dump");
        dir.mkdirs();
        Bukkit.getScheduler().scheduleSyncDelayedTask(this, new Runnable() { public void run() { dumpRegistry(); } }, 20L);
        Bukkit.getScheduler().scheduleSyncRepeatingTask(this, new Runnable() { public void run() { dumpTiles(); } }, 200L, 400L);
    }

    public void onDisable() { dumpTiles(); }

    static Object call(Object o, String m) {
        try { Method mm = o.getClass().getMethod(m); return mm.invoke(o); } catch (Throwable t) { return null; }
    }

    void dumpRegistry() {
        try {
            PrintWriter pw = new PrintWriter(new FileWriter(new File(dir, "items.tsv")));
            for (int i = 0; i < Item.byId.length; i++) {
                Item it = Item.byId[i];
                if (it == null) continue;
                StringBuilder sb = new StringBuilder();
                sb.append(i).append('\t').append(it.getClass().getName()).append('\t').append(safe(it.getName()))
                  .append('\t').append(it.getMaxDurability()).append('\t').append(it.getMaxStackSize());
                Object mc = call(it, "getMaxCharge");
                sb.append('\t').append(mc == null ? "" : mc.toString());
                Object tier = call(it, "getTier");
                sb.append('\t').append(tier == null ? "" : tier.toString());
                Set<String> seen = new LinkedHashSet<String>();
                for (int d = 0; d < 16; d++) {
                    try { String n = it.a(new ItemStack(i, 1, d)); if (n != null) seen.add(d + "=" + n); } catch (Throwable t) { }
                }
                sb.append('\t').append(seen.toString());
                pw.println(sb);
            }
            pw.close();
            pw = new PrintWriter(new FileWriter(new File(dir, "blocks.tsv")));
            for (int i = 0; i < Block.byId.length; i++) {
                Block b = Block.byId[i];
                if (b == null) continue;
                pw.println(i + "\t" + b.getClass().getName() + "\t" + safe(b.getName()) + "\t" + Block.lightBlock[i] + "\t" + Block.lightEmission[i] + "\t" + Block.n[i]);
            }
            pw.close();
            System.out.println("[Dumper] items dumped");
        } catch (Throwable t) { t.printStackTrace(); }
    }

    static String safe(String s) { return s == null ? "null" : s; }

    static String fieldVal(Object o, String name) {
        Class c = o.getClass();
        while (c != null) {
            try { Field f = c.getDeclaredField(name); f.setAccessible(true); return String.valueOf(f.get(o)); } catch (Throwable t) { }
            c = c.getSuperclass();
        }
        return "-";
    }

    void dumpTiles() {
        try {
            org.bukkit.World bw = Bukkit.getWorld("world");
            if (bw == null) return;
            World w = ((CraftWorld) bw).getHandle();
            PrintWriter pw = new PrintWriter(new FileWriter(new File(dir, "tiles.tsv"), true));
            pw.println("# time=" + w.getTime() + " count=" + w.tileEntityList.size());
            for (Object o : new ArrayList(w.tileEntityList)) {
                TileEntity te = (TileEntity) o;
                pw.println(te.getClass().getSimpleName() + "\t" + te.x + "\t" + te.y + "\t" + te.z + "\tblock=" + w.getTypeId(te.x, te.y, te.z) + ":" + w.getData(te.x, te.y, te.z)
                    + "\tenergy=" + fieldVal(te, "energy") + "\tfacing=" + fieldVal(te, "facing") + "\tactive=" + fieldVal(te, "active")
                    + "\tcable=" + fieldVal(te, "cableType") + "\tdir=" + fieldVal(te, "direction") + "\torient=" + fieldVal(te, "orientation")
                    + "\tprogress=" + fieldVal(te, "progress") + "\tsun=" + fieldVal(te, "collectorSunTime") + "\tscaled=" + fieldVal(te, "scaledEnergy"));
            }
            pw.close();
        } catch (Throwable t) { t.printStackTrace(); }
    }
}
