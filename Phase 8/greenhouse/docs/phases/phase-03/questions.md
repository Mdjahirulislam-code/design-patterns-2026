# Phase 3 — Abstract Factory questions

## A. Pattern

### 1. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently (`if format` for each piece) instead of as a family?

> [!NOTE]
> ***Your Answer***

 Abstract Factory creates a group of related objects that should work together as one family. In this greenhouse system, it makes sure that sensors and actuators belong to the same device family. If products are created independently, it is possible to create incompatible combinations, such as mixing simulation devices with edge devices that have different configurations.

---

### 2. Name the main participants (abstract factory, concrete factory, abstract products, concrete products, client). How does choosing a factory at the start commit the client to one family?

> [!NOTE]
> ***Your Answer***
The abstract factory defines methods for creating related devices. Concrete factories create specific device families, such as simulation or edge. Abstract products are general device types, while concrete products are actual devices like moisture sensors, light sensors, pumps, and lights. The client selects a factory first, so all created devices come from that selected family and keep compatible settings.

---

### 3. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?

> [!NOTE]
> ***Your Answer***
Abstract Factory should be used when multiple related products must be created together and their compatibility is important. It should be skipped when only one independent product is needed or when mixing different product types is acceptable.

---

# B. This phase of the application

### 4. In this lab, what is a device family, and what does `create_device_set()` (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?

> [!NOTE]
> ***Your Answer***
A device family is a group of related greenhouse devices with matching configurations. In this project, the families are simulation and edge. The device set creation method returns a complete kit containing related devices, such as sensors and actuators. Simulation and edge devices should not mix because they may use different protocols, configurations, and hardware behaviour.

---

### 5. Phase 2 Factory Method creators still exist. How does Abstract Factory compose them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?

> [!NOTE]
> ***Your Answer***
Abstract Factory uses the existing Phase 2 sensor creators internally instead of replacing them. This keeps sensor creation separated and easier to maintain. If sensor creators were removed, the family factory would become responsible for all construction logic and would lose separation of responsibilities.

---

### 6. Why add a `device_family` column on the existing `devices` table (with a default/backfill such as `"simulation"`) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?

> [!NOTE]
> ***Your Answer***
Adding `device_family` to the existing devices table keeps one unified device model and avoids duplicate tables for each family. Existing Phase 2 sensors can continue working without moving data. If the backfill is forgotten, old sensor rows will have missing family information and filtering or provisioning logic may not work correctly.

---

### 7. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). `GET /api/devices` can filter by `family` and `role`. Why must the UI be able to filter by family? Why do `/api/sensors` routes from Phase 2 still need to work?

> [!NOTE]
> ***Your Answer***
The UI needs family filtering so users can view only the selected device group, such as simulation or edge devices. The old `/api/sensors` routes must continue working because Phase 3 extends Phase 2 instead of breaking existing functionality.

---

# C. Compare, contrast, and scenarios

### 8. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which one product?” versus “which product line?” and mention that Abstract Factory often uses Factory Method–style methods inside.

> [!NOTE]
> ***Your Answer***
Factory Method focuses on creating one product while allowing subclasses to decide the exact object type. Abstract Factory focuses on creating a complete product line containing multiple related products. In this project, Factory Method creates individual sensors, while Abstract Factory creates a complete device family. Abstract Factory can use Factory Method-style creation methods internally.

---

### 9. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?

> [!NOTE]
> ***Your Answer***
Direct construction inside DTOs or HTTP handlers can create devices with incorrect combinations or missing default configurations. HTTP should only communicate with the service layer, which uses the abstract factory to create consistent device families.

---

### 10. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?

> [!NOTE]
> ***Your Answer***
A god factory mixes unrelated responsibilities and makes the system harder to maintain. Abstract Factory should only create related objects that belong to the same family. Locations, readings, and devices have different responsibilities and should have separate designs.
