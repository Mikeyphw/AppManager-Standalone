// SPDX-License-Identifier: GPL-3.0-or-later
package io.github.muntashirakon.AppManager.utils.appearance;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;

import android.content.Context;
import android.graphics.Color;

import androidx.appcompat.app.AppCompatDelegate;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import com.google.android.material.color.MaterialColors;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import io.github.muntashirakon.AppManager.settings.Prefs;

/** Theme acceptance against actual installed resources on the hosted emulator, no app-data restore. */
@RunWith(AndroidJUnit4.class)
public class Amui02ThemeInstrumentedTest {
    private int originalMode;
    private boolean originalPureBlack;

    @Before
    public void rememberPrefs() {
        originalMode = Prefs.Appearance.getNightMode();
        originalPureBlack = Prefs.Appearance.isPureBlackTheme();
    }

    @After
    public void restorePrefs() {
        Prefs.Appearance.setNightMode(originalMode);
        Prefs.Appearance.setPureBlackTheme(originalPureBlack);
    }

    private Context themed(boolean dark, boolean black) {
        Prefs.Appearance.setNightMode(dark
                ? AppCompatDelegate.MODE_NIGHT_YES : AppCompatDelegate.MODE_NIGHT_NO);
        Prefs.Appearance.setPureBlackTheme(black);
        return AppearanceUtils.getThemedContext(
                InstrumentationRegistry.getInstrumentation().getTargetContext(), false);
    }

    private int color(Context context, int attr) {
        return MaterialColors.getColor(context, attr, "AMUI02 instrumented theme");
    }

    @Test
    public void themeErrorColorUsesAppCompatAttributeInLightMode() {
        Context context = themed(false, false);
        assertEquals(color(context, androidx.appcompat.R.attr.colorError),
                ColorCodes.getFailureColor(context));
    }

    @Test
    public void themeErrorColorUsesAppCompatAttributeInDarkMode() {
        Context context = themed(true, false);
        assertEquals(color(context, androidx.appcompat.R.attr.colorError),
                ColorCodes.getFailureColor(context));
    }

    @Test
    public void darkPureBlackPaintsExactRootBlack() {
        Context context = themed(true, true);
        assertEquals(Color.BLACK, color(context, android.R.attr.colorBackground));
    }

    @Test
    public void darkPureBlackRetainsMaterialAccentAndRaisedSurface() {
        Context context = themed(true, true);
        assertNotEquals(Color.BLACK, color(context, androidx.appcompat.R.attr.colorPrimary));
        assertNotEquals(Color.BLACK, color(context, com.google.android.material.R.attr.colorSurface));
    }

    @Test
    public void blackPreferenceDoesNotForceBlackInLightMode() {
        Context context = themed(false, true);
        assertNotEquals(Color.BLACK, color(context, android.R.attr.colorBackground));
    }

    @Test
    public void regularDarkThemeKeepsSurfaceAsBackground() {
        Context context = themed(true, false);
        assertEquals(color(context, com.google.android.material.R.attr.colorSurface),
                color(context, android.R.attr.colorBackground));
    }
}
