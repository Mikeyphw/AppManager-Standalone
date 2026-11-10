// SPDX-License-Identifier: GPL-3.0-or-later
package io.github.muntashirakon.AppManager.utils.appearance;

import static org.junit.Assert.*;

import android.app.WallpaperManager;
import android.app.WallpaperColors;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.os.Build;
import android.os.SystemClock;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import com.google.android.material.color.DynamicColors;
import com.google.android.material.color.MaterialColors;

import org.junit.Test;
import org.junit.runner.RunWith;

/** Hosted-disposable-emulator-only wallpaper mutation. NEVER run on a person's phone. */
@RunWith(AndroidJUnit4.class)
public class Amui05WallpaperInstrumentedTest {
    private Context application() {return InstrumentationRegistry.getInstrumentation().getTargetContext();}
    @Test public void actualWallpaperColorSourceChangesOnHostedEmulator() throws Exception {
        assertTrue("AMUI05_HARD_REFUSAL_PHYSICAL_WALLPAPER_MUTATION",
                Build.HARDWARE.contains("ranchu") || Build.FINGERPRINT.contains("generic"));
        assertTrue("AMUI05_WALLPAPER_REQUIRES_ANDROID12", Build.VERSION.SDK_INT >= 31);
        WallpaperManager manager = WallpaperManager.getInstance(application());
        assertTrue("AMUI05_SYSTEM_WALLPAPER_MUTATION_UNSUPPORTED", manager.isWallpaperSupported());
        WallpaperColors[] observed = new WallpaperColors[2];
        int[] observedAccent = new int[2];
        for (int i = 0; i < 2; i++) {
            int shade = i == 0 ? Color.rgb(224, 48, 48) : Color.rgb(32, 64, 224);
            Bitmap bitmap = Bitmap.createBitmap(320, 320, Bitmap.Config.ARGB_8888);
            bitmap.eraseColor(shade);
            try { manager.setBitmap(bitmap, null, true, WallpaperManager.FLAG_SYSTEM); }
            finally {bitmap.recycle();}
            for (int retry = 0; retry < 35; retry++) {
                WallpaperColors next = manager.getWallpaperColors(WallpaperManager.FLAG_SYSTEM);
                if (next != null && next.getPrimaryColor() != null &&
                        (i == 0 || !next.getPrimaryColor().equals(observed[0].getPrimaryColor()))) {
                    observed[i] = next; break;
                }
                SystemClock.sleep(1000);
            }
            assertNotNull("AMUI05_WALLPAPER_SERVICE_COLOR_NOT_UPDATED", observed[i]);
            // A changed WallpaperColors object alone is NOT proof that app colors
            // recomposed. Require a newly wrapped Material primary role to follow.
            for (int retry = 0; retry < 40; retry++) {
                Context themed = AppearanceUtils.getThemedContext(application(), false);
                int next = MaterialColors.getColor(themed,
                        androidx.appcompat.R.attr.colorPrimary, "AMUI05 wallpaper-derived primary");
                if (i == 0 || next != observedAccent[0]) {
                    observedAccent[i] = next;
                    break;
                }
                SystemClock.sleep(1000);
            }
            assertNotEquals("AMUI05_PALETTE_RECOLOR_NOT_OBSERVED", Color.TRANSPARENT, observedAccent[i]);
        }
        assertNotEquals("AMUI05_WALLPAPER_PALETTE_DID_NOT_CHANGE",
                observed[0].getPrimaryColor(), observed[1].getPrimaryColor());
        assertNotEquals("AMUI05_DYNAMIC_ACCENT_DID_NOT_CHANGE",
                observedAccent[0], observedAccent[1]);
    }
    @Test public void currentWallpaperProvidesDynamicThemeRole() {
        assertTrue("AMUI05_PHYSICAL_REFUSED", Build.HARDWARE.contains("ranchu") || Build.FINGERPRINT.contains("generic"));
        assertTrue("AMUI05_DYNAMIC_UNAVAILABLE", DynamicColors.isDynamicColorAvailable());
        Context context = AppearanceUtils.getThemedContext(application(), false);
        assertNotEquals(Color.TRANSPARENT, MaterialColors.getColor(context,
                androidx.appcompat.R.attr.colorPrimary, "AMUI05 dynamic primary"));
    }
}
