# AMUI-02 HF05 — AppCompat semantic error role

The hosted Android build on `edb0d4861818e77253ecd6478481a12fa197480f` failed at
`app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/ColorCodes.java:44`
with `cannot find symbol colorError` in `com.google.android.material.R.attr`.

AppCompat owns `colorError` under non-transitive R classes. Resolve with
`androidx.appcompat.R.attr.colorError` through `MaterialColors.getColor`.
Do not disable lint, instrumentation, or wallpaper-derived colors.

Source contracts and regression tests now guard correct namespace and reject
fixed color substitutes. Android 15/16 instrumentation checks the resolved role.
