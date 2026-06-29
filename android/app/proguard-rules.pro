# kotlinx.serialization — conservar los serializadores generados.
-keepclassmembers class **$$serializer { *; }
-keepclasseswithmembers class mx.recetia.app.data.model.** { *; }
-keep,includedescriptorclasses class mx.recetia.app.data.model.**$$serializer { *; }
