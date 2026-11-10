// SPDX-License-Identifier: GPL-3.0-or-later
package io.github.muntashirakon.AppManager.utils.appearance;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.os.Environment;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatDelegate;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import com.google.android.material.chip.Chip;
import com.google.android.material.color.MaterialColors;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

import io.github.muntashirakon.AppManager.R;
import io.github.muntashirakon.AppManager.settings.Prefs;

/** AMUI-04A: real on-device Material render fixtures, never screenshots of private apps. */
@RunWith(AndroidJUnit4.class)
public class Amui04AVisualInstrumentedTest {
    private int originalNightMode;
    private boolean originalBlack;

    @Before
    public void retainSettings() {
        originalNightMode = Prefs.Appearance.getNightMode();
        originalBlack = Prefs.Appearance.isPureBlackTheme();
    }

    @After
    public void restoreSettings() {
        Prefs.Appearance.setNightMode(originalNightMode);
        Prefs.Appearance.setPureBlackTheme(originalBlack);
    }

    private Context themed(boolean dark, boolean black) {
        Prefs.Appearance.setNightMode(dark ? AppCompatDelegate.MODE_NIGHT_YES
                : AppCompatDelegate.MODE_NIGHT_NO);
        Prefs.Appearance.setPureBlackTheme(black);
        return AppearanceUtils.getThemedContext(
                InstrumentationRegistry.getInstrumentation().getTargetContext(), false);
    }

    private int color(Context context, int attribute) {
        return MaterialColors.getColor(context, attribute, "AMUI04A visual palette");
    }

    @Test
    public void lightPaletteNeverGetsForcedBlack() {
        Context context = themed(false, true);
        assertNotEquals(Color.BLACK, color(context, android.R.attr.colorBackground));
        assertNotEquals(Color.TRANSPARENT, color(context, androidx.appcompat.R.attr.colorPrimary));
    }

    @Test
    public void regularDarkBackgroundFollowsTonalSurface() {
        Context context = themed(true, false);
        assertEquals(color(context, com.google.android.material.R.attr.colorSurface),
                color(context, android.R.attr.colorBackground));
    }

    @Test
    public void blackRootPreservesMaterialAccentsAndError() {
        Context context = themed(true, true);
        assertEquals(Color.BLACK, color(context, android.R.attr.colorBackground));
        assertNotEquals(Color.BLACK, color(context, androidx.appcompat.R.attr.colorPrimary));
        assertNotEquals(Color.BLACK, color(context, androidx.appcompat.R.attr.colorError));
        assertNotEquals(Color.BLACK, color(context, com.google.android.material.R.attr.colorSurface));
    }

    @Test
    public void quickFiltersAndBoundRowInflateUnderDifferentPalettes() {
        for (boolean dark : new boolean[] {false, true}) {
            Context context = themed(dark, dark);
            View chips = LayoutInflater.from(context).inflate(R.layout.amui03c_quick_filters, null, false);
            View row = LayoutInflater.from(context).inflate(R.layout.item_main, null, false);
            assertNotNull(chips.findViewById(R.id.amui03c_advanced));
            Chip user = chips.findViewById(R.id.amui03c_user);
            assertNotNull(user);
            assertTrue(user.isCheckable());
            assertNotNull(row.findViewById(R.id.packageName));
            assertNotNull(row.findViewById(R.id.favorite_icon));
        }
    }

    private Bitmap renderFixture(Context context) {
        final Bitmap[] rendered = new Bitmap[1];
        // Inflate, measure, lay out and draw Android views on the actual UI thread.
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            final int width = 1080;
            LinearLayout root = new LinearLayout(context);
            root.setOrientation(LinearLayout.VERTICAL);
            root.setBackgroundColor(color(context, android.R.attr.colorBackground));
            View filters = LayoutInflater.from(context).inflate(R.layout.amui03c_quick_filters, root, false);
            View row = LayoutInflater.from(context).inflate(R.layout.item_main, root, false);
            TextView label = row.findViewById(R.id.label);
            TextView packageName = row.findViewById(R.id.packageName);
            TextView version = row.findViewById(R.id.version);
            TextView isSystem = row.findViewById(R.id.isSystem);
            label.setText("AppManager visual fixture");
            packageName.setText("io.github.muntashirakon.AppManager.fixture");
            version.setText("v1.0");
            isSystem.setText("User");
            root.addView(filters);
            root.addView(row);
            root.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                    View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
            int height = root.getMeasuredHeight();
            assertTrue("Rendered UI fixture height is invalid", height >= 100 && height <= 3200);
            root.layout(0, 0, width, height);
            Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
            Canvas canvas = new Canvas(bitmap);
            root.draw(canvas);
            assertEquals(width, bitmap.getWidth());
            rendered[0] = bitmap;
        });
        assertNotNull(rendered[0]);
        return rendered[0];
    }

    private void snapshot(String name, boolean dark, boolean black) throws IOException {
        Context context = themed(dark, black);
        File external = InstrumentationRegistry.getInstrumentation().getTargetContext()
                .getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        assertNotNull("External app-scoped picture directory unavailable", external);
        File outputDirectory = new File(external, "amui04a");
        assertTrue("Cannot create screenshot directory", outputDirectory.isDirectory()
                || outputDirectory.mkdirs());
        File output = new File(outputDirectory, name + ".png");
        Bitmap bitmap = renderFixture(context);
        try (FileOutputStream stream = new FileOutputStream(output)) {
            assertTrue("PNG encoding failed", bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream));
            stream.flush();
        } finally {
            bitmap.recycle();
        }
        assertTrue("Screenshot file missing or empty", output.isFile() && output.length() > 1024);
    }

    @Test
    public void captureThreeRealRenderedPaletteFixtures() throws IOException {
        snapshot("light", false, false);
        snapshot("dark", true, false);
        snapshot("pure-black", true, true);
    }
}
