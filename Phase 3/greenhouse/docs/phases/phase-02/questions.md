A. Pattern
1. State the intent of Factory Method. What problem appears when constructors are spread around?

Ans:
Factory Method keeps object creation in one place. It avoids making every part of the program know how different objects are created. If constructors or many if/elif checks are everywhere, adding new types becomes harder and can create inconsistent code.

2. Name the main participants of Factory Method.


Ans:
The product is the common object that the application uses.
A concrete product is a specific type of that object.
The creator defines the method for creating the product.
A concrete creator decides which specific product to create and its default values.
The client uses the creator instead of creating objects directly.

3. How do you add a new product variant?


Ans:
With separate creators, I can add a new creator class and register it without changing existing creators. With a large if/elif function, every new type requires editing the same function, which makes it harder to maintain.

B. This phase of the application
4. What is the product and what are the concrete creators?


Ans:
The product is the Sensor object. The concrete creators are MoistureSensorCreator and LightSensorCreator. The API uses the creator system because it should not know how each sensor is created or what default settings it needs.

5. Why are type and device_type different?


Ans:
The type value is a simple input from the user, like "moisture" or "light". The creator converts it into the stored device_type, such as "moisture_sensor", and also decides the correct default_config.

6. Why use one devices table instead of a sensors table?


Ans:
A common devices table makes it easier to add more device types later. Sensors use role="sensor" now, and future phases can add actuators without creating a completely new database structure.

7. What happens with an unknown type?


Ans:
The system should reject it and return an error before saving anything. The registry or service should handle this because they know which creators are available. The router should only handle the HTTP response.

C. Compare, contrast, and scenarios
8. Factory Method vs simple factory.


Ans:
A simple factory is okay when there are only a few small object types. Factory Method is better when the system may grow because each object type has its own creator and the code stays easier to extend.

9. Factory Method vs Abstract Factory.


Ans:
Factory Method decides which single object should be created. Abstract Factory creates a group of related objects. Phase 2 only creates sensors, so Factory Method is enough. Phase 3 needs Abstract Factory because it adds related device families.

10. Why should creators not handle database or HTTP work?

Ans:
The creator should only be responsible for creating sensors. Adding SQLAlchemy or FastAPI code would mix responsibilities. Database work belongs in the infrastructure layer, and HTTP handling belongs in the API layer.