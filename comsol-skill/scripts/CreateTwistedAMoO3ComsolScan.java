import com.comsol.model.*;
import com.comsol.model.util.*;

/** COMSOL 6.0 template for a normal-incidence twisted alpha-MoO3 bilayer scan. */
public class CreateTwistedAMoO3ComsolScan {
  public static Model run() throws Exception {
    Model m = ModelUtil.create("TwistedAMoO3ComsolScan");
    m.label("Twisted alpha-MoO3 LCP/RCP transmission");

    m.param().set("lambda_min", "8[um]");
    m.param().set("lambda_max", "24[um]");
    m.param().set("film_L", "5[um]");
    m.param().set("d_bottom", "1[um]");
    m.param().set("d_top", "1[um]");
    m.param().set("air_t", "2[um]");
    m.param().set("twist", "45[deg]");
    m.param().set("pol", "1", "+1/-1 circular source convention");

    m.param().set("epsinf_x", "4");
    m.param().set("epsinf_y", "5.2");
    m.param().set("epsinf_z", "2.4");
    m.param().set("wLO_x", "1.8322e14[rad/s]");
    m.param().set("wLO_y", "1.6041e14[rad/s]");
    m.param().set("wLO_z", "1.8925e14[rad/s]");
    m.param().set("wTO_x", "1.5457e14[rad/s]");
    m.param().set("wTO_y", "1.0273e14[rad/s]");
    m.param().set("wTO_z", "1.8058e14[rad/s]");
    m.param().set("gamma_x", "7.5398e11[rad/s]");
    m.param().set("gamma_y", "7.5398e11[rad/s]");
    m.param().set("gamma_z", "3.7699e11[rad/s]");

    m.component().create("comp1", true);
    GeomSequence g = m.component("comp1").geom().create("geom1", 3);
    g.lengthUnit("um");
    block(g, "air_bottom", "Air below stack", new String[]{"film_L", "film_L", "air_t"}, new String[]{"0", "0", "-air_t/2"});
    block(g, "bottom", "Bottom alpha-MoO3", new String[]{"film_L", "film_L", "d_bottom"}, new String[]{"0", "0", "d_bottom/2"});
    block(g, "top", "Top alpha-MoO3, rotated", new String[]{"film_L", "film_L", "d_top"}, new String[]{"0", "0", "d_bottom+d_top/2"});
    block(g, "air_top", "Air above stack", new String[]{"film_L", "film_L", "air_t"}, new String[]{"0", "0", "d_bottom+d_top+air_t/2"});
    g.run();

    explicit(m, "air_dom", 3, new int[]{1, 4});
    explicit(m, "bottom_dom", 3, new int[]{2});
    explicit(m, "top_dom", 3, new int[]{3});
    box(m, "source_bnd", 2, "d_bottom+d_top+air_t-1[nm]", "d_bottom+d_top+air_t+1[nm]");
    box(m, "receiver_bnd", 2, "-air_t-1[nm]", "-air_t+1[nm]");
    sideBox(m, "xneg", "-film_L/2-1[nm]", "-film_L/2+1[nm]", "-film_L/2", "film_L/2");
    sideBox(m, "xpos", "film_L/2-1[nm]", "film_L/2+1[nm]", "-film_L/2", "film_L/2");
    sideBox(m, "yneg", "-film_L/2", "film_L/2", "-film_L/2-1[nm]", "-film_L/2+1[nm]");
    sideBox(m, "ypos", "-film_L/2", "film_L/2", "film_L/2-1[nm]", "film_L/2+1[nm]");

    m.component("comp1").mesh().create("mesh1");
    m.component("comp1").mesh("mesh1").automatic(false);
    m.component("comp1").mesh("mesh1").create("size1", "Size");
    m.component("comp1").mesh("mesh1").feature("size1").selection().geom("geom1", 2);
    m.component("comp1").mesh("mesh1").feature("size1").selection().set(new int[]{3});
    m.component("comp1").mesh("mesh1").feature("size1").set("hmax", "1[um]");
    m.component("comp1").mesh("mesh1").feature("size1").set("hmin", "0.5[um]");
    m.component("comp1").mesh("mesh1").feature().remove("ftet1");
    m.component("comp1").mesh("mesh1").create("map1", "Map");
    m.component("comp1").mesh("mesh1").feature("map1").selection().set(new int[]{3});
    m.component("comp1").mesh("mesh1").create("swe1", "Sweep");
    m.component("comp1").mesh("mesh1").feature("swe1").selection().set(new int[]{1, 2, 3, 4});
    m.component("comp1").mesh("mesh1").feature("swe1").create("dis1", "Distribution");
    m.component("comp1").mesh("mesh1").feature("swe1").feature("dis1").selection().set(new int[]{1});
    m.component("comp1").mesh("mesh1").feature("swe1").feature("dis1").set("numelem", 4);
    m.component("comp1").mesh("mesh1").run();

    material(m, "air", "Air", "air_dom", new String[]{"1", "1", "1"});
    String w = "2*pi*freq";
    // COMSOL exp(+i*omega*t): passive Lorentz loss uses +i*omega*gamma here.
    String ex = lorentz("x", w);
    String ey = lorentz("y", w);
    String ez = lorentz("z", w);
    material(m, "amo3_bottom", "alpha-MoO3 bottom", "bottom_dom", new String[]{ex, ey, ez});
    String c2 = "cos(twist)^2", s2 = "sin(twist)^2", cs = "sin(twist)*cos(twist)";
    String exx = "(" + ex + ")*" + c2 + "+(" + ey + ")*" + s2;
    String eyy = "(" + ex + ")*" + s2 + "+(" + ey + ")*" + c2;
    String exy = "((" + ex + ")-(" + ey + "))*" + cs;
    material(m, "amo3_top", "alpha-MoO3 top, explicit rotated tensor", "top_dom",
      new String[]{exx, exy, "0", exy, eyy, "0", "0", "0", ez});

    m.component("comp1").physics().create("ewfd", "ElectromagneticWavesFrequencyDomain", "geom1");
    m.component("comp1").physics("ewfd").feature("wee1").set("DisplacementFieldModel", "RelativePermittivity");
    m.component("comp1").physics("ewfd").feature("wee1").set("epsilonr_mat", "from_mat");
    m.component("comp1").physics("ewfd").feature("wee1").set("coordinateSystem", "GlobalSystem");
    periodicPair(m, "pcx1", 1, 18); periodicPair(m, "pcx2", 4, 19);
    periodicPair(m, "pcx3", 7, 20); periodicPair(m, "pcx4", 10, 21);
    periodicPair(m, "pcy1", 2, 14); periodicPair(m, "pcy2", 5, 15);
    periodicPair(m, "pcy3", 8, 16); periodicPair(m, "pcy4", 11, 17);

    m.component("comp1").physics("ewfd").create("circsrc", "Scattering", 2);
    m.component("comp1").physics("ewfd").feature("circsrc").selection().named("source_bnd");
    m.component("comp1").physics("ewfd").feature("circsrc").set("IncidentField", "EField");
    m.component("comp1").physics("ewfd").feature("circsrc").set("E0i", new String[]{"1/sqrt(2)[V/m]", "pol*i/sqrt(2)[V/m]", "0"});
    m.component("comp1").physics("ewfd").create("rxsctr", "Scattering", 2);
    m.component("comp1").physics("ewfd").feature("rxsctr").selection().named("receiver_bnd");

    m.component("comp1").cpl().create("intop_rx", "Integration");
    m.component("comp1").cpl("intop_rx").selection().named("receiver_bnd");
    m.component("comp1").variable().create("var1");
    m.component("comp1").variable("var1").set("Pinc", "0.5*(1[V/m])^2/376.730313668[ohm]*film_L^2");
    m.component("comp1").variable("var1").set("Ptrans", "-intop_rx(ewfd.Poavz)");
    m.component("comp1").variable("var1").set("Tcomsol", "Ptrans/Pinc");

    m.study().create("std1");
    m.study("std1").label("8-24 um, 161-point frequency sweep");
    m.study("std1").create("freq", "Frequency");
    m.study("std1").feature("freq").set("plist", "range(c_const/lambda_max,(c_const/lambda_min-c_const/lambda_max)/160,c_const/lambda_min)");
    m.result().numerical().create("gev1", "EvalGlobal");
    m.result().numerical("gev1").set("expr", new String[]{"Tcomsol"});
    m.result().numerical("gev1").set("unit", new String[]{"1"});
    return m;
  }

  private static String lorentz(String axis, String w) {
    return "epsinf_" + axis + "*(1+(wLO_" + axis + "^2-wTO_" + axis + "^2)/(wTO_" + axis + "^2-(" + w + ")^2+i*(" + w + ")*gamma_" + axis + "))";
  }

  private static void block(GeomSequence g, String tag, String label, String[] size, String[] pos) {
    g.create(tag, "Block"); g.feature(tag).label(label); g.feature(tag).set("base", "center");
    g.feature(tag).set("size", size); g.feature(tag).set("pos", pos);
  }

  private static void explicit(Model m, String tag, int dim, int[] ids) {
    m.component("comp1").selection().create(tag, "Explicit");
    m.component("comp1").selection(tag).geom("geom1", dim);
    m.component("comp1").selection(tag).set(ids);
  }

  private static void box(Model m, String tag, int dim, String zmin, String zmax) {
    m.component("comp1").selection().create(tag, "Box");
    m.component("comp1").selection(tag).geom("geom1", dim);
    m.component("comp1").selection(tag).set("condition", "inside");
    m.component("comp1").selection(tag).set("xmin", "-film_L/2");
    m.component("comp1").selection(tag).set("xmax", "film_L/2");
    m.component("comp1").selection(tag).set("ymin", "-film_L/2");
    m.component("comp1").selection(tag).set("ymax", "film_L/2");
    m.component("comp1").selection(tag).set("zmin", zmin);
    m.component("comp1").selection(tag).set("zmax", zmax);
  }

  private static void sideBox(Model m, String tag, String xmin, String xmax, String ymin, String ymax) {
    m.component("comp1").selection().create(tag, "Box");
    m.component("comp1").selection(tag).geom("geom1", 2);
    m.component("comp1").selection(tag).set("condition", "inside");
    m.component("comp1").selection(tag).set("xmin", xmin); m.component("comp1").selection(tag).set("xmax", xmax);
    m.component("comp1").selection(tag).set("ymin", ymin); m.component("comp1").selection(tag).set("ymax", ymax);
    m.component("comp1").selection(tag).set("zmin", "-air_t");
    m.component("comp1").selection(tag).set("zmax", "d_bottom+d_top+air_t");
  }

  private static void periodicPair(Model m, String tag, int a, int b) {
    m.component("comp1").physics("ewfd").create(tag, "PeriodicCondition", 2);
    m.component("comp1").physics("ewfd").feature(tag).selection().set(new int[]{a, b});
    m.component("comp1").physics("ewfd").feature(tag).set("PeriodicType", "Continuity");
  }

  private static void material(Model m, String tag, String label, String selection, String[] eps) {
    m.component("comp1").material().create(tag, "Common");
    m.component("comp1").material(tag).label(label);
    m.component("comp1").material(tag).selection().named(selection);
    m.component("comp1").material(tag).propertyGroup("def").set("relpermittivity", eps);
    m.component("comp1").material(tag).propertyGroup("def").set("relpermeability", new String[]{"1"});
    m.component("comp1").material(tag).propertyGroup("def").set("electricconductivity", new String[]{"0"});
  }

  public static void main(String[] args) throws Exception { run(); }
}
