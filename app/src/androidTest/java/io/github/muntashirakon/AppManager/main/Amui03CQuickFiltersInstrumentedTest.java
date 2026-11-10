// SPDX-License-Identifier: GPL-3.0-or-later
package io.github.muntashirakon.AppManager.main;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import com.google.android.material.chip.Chip;

import org.junit.Test;
import org.junit.runner.RunWith;

import io.github.muntashirakon.AppManager.R;
import io.github.muntashirakon.AppManager.utils.appearance.AppearanceUtils;

/** Read-only API35/API36 view inflation; no app data, profiles or permissions changed. */
@RunWith(AndroidJUnit4.class)
public class Amui03CQuickFiltersInstrumentedTest {
    private View inflateFilters() {
        Context context = AppearanceUtils.getThemedContext(
                InstrumentationRegistry.getInstrumentation().getTargetContext(), false);
        return LayoutInflater.from(context).inflate(R.layout.amui03c_quick_filters, null, false);
    }

    @Test
    public void allQuickFiltersInflateAndAreCheckable() {
        View view = inflateFilters();
        int[] ids = {R.id.amui03c_all, R.id.amui03c_user, R.id.amui03c_system,
                R.id.amui03c_frozen, R.id.amui03c_backed_up, R.id.amui03c_display_mode};
        for (int id : ids) {
            Chip chip = view.findViewById(id);
            assertNotNull("Missing quick filter " + id, chip);
            assertTrue(chip.isCheckable());
        }
    }

    @Test
    public void advancedAndSummaryControlsInflate() {
        View view = inflateFilters();
        Chip advanced = view.findViewById(R.id.amui03c_advanced);
        assertNotNull(advanced);
        assertTrue(!advanced.isCheckable());
        assertNotNull(view.findViewById(R.id.amui03c_summary));
    }

    @Test
    public void quickChipSelectionCanToggleWithoutChangingPackages() {
        // ChipGroup uses a main-thread CheckedStateTracker. Detached, off-thread
        // mutation is not representative of real UI interaction on API35/36.
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            View view = inflateFilters();
            com.google.android.material.chip.ChipGroup group =
                    view.findViewById(R.id.amui03c_chips);
            assertNotNull("Chip group missing", group);
            assertFalse("A filter must be allowed to deselect", group.isSelectionRequired());
            Chip user = view.findViewById(R.id.amui03c_user);
            assertNotNull("User quick chip missing", user);
            assertTrue("User quick chip must be checkable", user.isCheckable());
            user.setChecked(true);
            assertTrue("Main-thread check did not stick", user.isChecked());
            user.setChecked(false);
            assertFalse("Main-thread uncheck did not stick", user.isChecked());
        });
        InstrumentationRegistry.getInstrumentation().waitForIdleSync();
    }
}
