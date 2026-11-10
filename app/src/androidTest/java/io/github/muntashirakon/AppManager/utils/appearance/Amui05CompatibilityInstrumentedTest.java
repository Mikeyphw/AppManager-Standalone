// SPDX-License-Identifier: GPL-3.0-or-later
package io.github.muntashirakon.AppManager.utils.appearance;

import static org.junit.Assert.*;

import android.content.Context;
import android.content.res.Configuration;
import android.graphics.Color;
import android.os.Build;
import android.view.LayoutInflater;
import android.view.View;

import androidx.appcompat.app.AppCompatDelegate;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import com.google.android.material.chip.Chip;
import com.google.android.material.color.DynamicColors;
import com.google.android.material.color.MaterialColors;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import io.github.muntashirakon.AppManager.R;
import io.github.muntashirakon.AppManager.settings.Prefs;

/** AMUI05: read-only M3 compatibility, including API 30 fallback. No package or user mutation. */
@RunWith(AndroidJUnit4.class)
public class Amui05CompatibilityInstrumentedTest {
    private int previousNight;
    private boolean previousBlack;

    @Before public void savePreferences() {
        previousNight = Prefs.Appearance.getNightMode();
        previousBlack = Prefs.Appearance.isPureBlackTheme();
    }
    @After public void restorePreferences() {
        Prefs.Appearance.setNightMode(previousNight);
        Prefs.Appearance.setPureBlackTheme(previousBlack);
    }
    private Context theme(boolean dark, boolean black) {
        Prefs.Appearance.setNightMode(dark ? AppCompatDelegate.MODE_NIGHT_YES : AppCompatDelegate.MODE_NIGHT_NO);
        Prefs.Appearance.setPureBlackTheme(black);
        return AppearanceUtils.getThemedContext(InstrumentationRegistry.getInstrumentation().getTargetContext(), false);
    }
    private int color(Context context, int attr) {
        return MaterialColors.getColor(context, attr, "AMUI05 verified Material theme role");
    }
    @Test public void olderAndroidNeverClaimsSystemWallpaperDynamicPalette() {
        Context context = theme(false, false);
        if (Build.VERSION.SDK_INT < 31) {
            assertFalse("API30 must use deterministic Material fallback", DynamicColors.isDynamicColorAvailable());
        }
        assertNotEquals(Color.TRANSPARENT, color(context, androidx.appcompat.R.attr.colorPrimary));
    }
    @Test public void lightRootUsesNonBlackSemanticSurface() {
        Context context = theme(false, true);
        assertNotEquals(Color.BLACK, color(context, android.R.attr.colorBackground));
        assertNotEquals(Color.TRANSPARENT, color(context, com.google.android.material.R.attr.colorSurface));
    }
    @Test public void darkRootPreservesMaterialSurfaceAndError() {
        Context context = theme(true, false);
        assertEquals(color(context, com.google.android.material.R.attr.colorSurface), color(context, android.R.attr.colorBackground));
        assertNotEquals(Color.TRANSPARENT, color(context, androidx.appcompat.R.attr.colorError));
    }
    @Test public void pureBlackOnlyOverridesBackgroundNotAccent() {
        Context context = theme(true, true);
        assertEquals(Color.BLACK, color(context, android.R.attr.colorBackground));
        assertNotEquals(Color.BLACK, color(context, androidx.appcompat.R.attr.colorPrimary));
        assertNotEquals(Color.BLACK, color(context, com.google.android.material.R.attr.colorSurface));
    }
    @Test public void widgetAndDialogContextsKeepRaisedSurface() {
        theme(true, true);
        Context context = AppearanceUtils.getThemedWidgetContext(InstrumentationRegistry.getInstrumentation().getTargetContext(), false);
        assertEquals(Color.BLACK, color(context, android.R.attr.colorBackground));
        assertNotEquals(Color.BLACK, color(context, com.google.android.material.R.attr.colorSurface));
    }
    @Test public void quickFilterChipCanToggleAfterConfigurationInflation() {
        // Only real UI-thread mutations count as chip acceptance.
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            for (boolean dark : new boolean[]{false, true}) {
                Context context = theme(dark, false);
                View root = LayoutInflater.from(context).inflate(R.layout.amui03c_quick_filters, null, false);
                Chip user = root.findViewById(R.id.amui03c_user);
                assertNotNull(user);
                assertTrue(user.isCheckable());
                user.setChecked(true);
                assertTrue(user.isChecked());
                user.setChecked(false);
                assertFalse(user.isChecked());
            }
        });
    }
    @Test public void representativeRowInflatesWithSelectedMode() {
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            Context context = theme(false, false);
            View row = LayoutInflater.from(context).inflate(R.layout.item_main, null, false);
            assertNotNull(row.findViewById(R.id.packageName));
            assertNotNull(row.findViewById(R.id.favorite_icon));
        });
    }
}
