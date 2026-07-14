import com.comsol.model.*;
import com.comsol.model.util.*;

/** Export Tcomsol from two solved models using environment-configured paths. */
public class ExportComsolTransmission {
  public static void main(String[] args) throws Exception {
    exportOne("lcp", required("COMSOL_LCP_MODEL"), required("COMSOL_LCP_TABLE"));
    exportOne("rcp", required("COMSOL_RCP_MODEL"), required("COMSOL_RCP_TABLE"));
  }

  private static String required(String name) {
    String value = System.getenv(name);
    if (value == null || value.isEmpty()) throw new IllegalArgumentException("Set " + name);
    return value;
  }

  private static void exportOne(String tag, String modelPath, String outputPath) throws Exception {
    Model m = ModelUtil.load(tag, modelPath);
    m.result().table().create("tbl_export", "Table");
    m.result().numerical().create("gev_export", "EvalGlobal");
    m.result().numerical("gev_export").set("data", "dset1");
    m.result().numerical("gev_export").set("expr", new String[]{"Tcomsol"});
    m.result().numerical("gev_export").set("descr", new String[]{"COMSOL transmitted power ratio"});
    m.result().numerical("gev_export").set("table", "tbl_export");
    m.result().numerical("gev_export").setResult();
    m.result().table("tbl_export").save(outputPath);
    ModelUtil.remove(tag);
  }
}
