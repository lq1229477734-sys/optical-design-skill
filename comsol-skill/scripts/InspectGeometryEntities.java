import com.comsol.model.*;
import com.comsol.model.util.*;
import java.util.Arrays;

/** Set COMSOL_MODEL to an .mph path, then run this class through comsolbatch. */
public class InspectGeometryEntities {
  public static void main(String[] args) throws Exception {
    String path = System.getenv("COMSOL_MODEL");
    if (path == null || path.isEmpty()) throw new IllegalArgumentException("Set COMSOL_MODEL");
    Model m = ModelUtil.load("inspect", path);
    GeomMeasureFinal q = m.component("comp1").geom("geom1").measureFinal();
    print(q, 2, 256, "boundary");
    print(q, 1, 512, "edge");
  }

  private static void print(GeomMeasureFinal q, int dim, int limit, String label) {
    for (int id = 1; id <= limit; id++) {
      try {
        q.selection().geom(dim);
        q.selection().set(new int[]{id});
        System.out.println(label + " " + id + " measure=" + q.getVolume() + " bbox=" + Arrays.toString(q.getBoundingBox()));
      } catch (Exception ignored) {
        break;
      }
    }
  }
}
