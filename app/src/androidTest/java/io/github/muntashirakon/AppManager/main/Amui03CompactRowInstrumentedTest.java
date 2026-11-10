// SPDX-License-Identifier: GPL-3.0-or-later
package io.github.muntashirakon.AppManager.main;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import com.google.android.material.card.MaterialCardView;

import org.junit.Test;
import org.junit.runner.RunWith;

import io.github.muntashirakon.AppManager.R;
import io.github.muntashirakon.AppManager.utils.appearance.AppearanceUtils;
import io.github.muntashirakon.view.AutoFitGridLayoutManager;

/** Read-only UI inflation smoke test; does not modify packages or profiles. */
@RunWith(AndroidJUnit4.class)
public class Amui03CompactRowInstrumentedTest {
    @Test
    public void compactRowRetainsAllAdapterBoundViews() {
        Context context = AppearanceUtils.getThemedContext(
                InstrumentationRegistry.getInstrumentation().getTargetContext(), false);
        View view = LayoutInflater.from(context).inflate(R.layout.item_main, null, false);
        assertTrue(view instanceof MaterialCardView);
        MaterialCardView card = (MaterialCardView) view;
        assertTrue(card.isClickable());
        assertTrue(card.isFocusable());
        assertTrue(card.isCheckable());
        int[] ids = {
                R.id.icon, R.id.backup_indicator, R.id.favorite_icon, R.id.label,
                R.id.packageName, R.id.version, R.id.isSystem, R.id.size,
                R.id.date, R.id.shareid, R.id.issuer, R.id.sha,
                R.id.backup_info, R.id.backup_info_ext
        };
        for (int id : ids) assertNotNull("Required bound field " + id, view.findViewById(id));
    }
    @Test
    public void spanCountTracksCompactWidthBoundaries() {
        assertEquals(1, AutoFitGridLayoutManager.calculateSpanCount(0, 480));
        assertEquals(1, AutoFitGridLayoutManager.calculateSpanCount(479, 480));
        assertEquals(1, AutoFitGridLayoutManager.calculateSpanCount(480, 480));
        assertEquals(1, AutoFitGridLayoutManager.calculateSpanCount(959, 480));
        assertEquals(2, AutoFitGridLayoutManager.calculateSpanCount(960, 480));
        assertEquals(3, AutoFitGridLayoutManager.calculateSpanCount(1440, 480));
        assertEquals(1, AutoFitGridLayoutManager.calculateSpanCount(1000, 0));
    }

    @Test
    public void cardCheckableStateStillRespondsToSelection() {
        Context context = AppearanceUtils.getThemedContext(
                InstrumentationRegistry.getInstrumentation().getTargetContext(), false);
        MaterialCardView card = (MaterialCardView) LayoutInflater.from(context)
                .inflate(R.layout.item_main, null, false);
        card.setChecked(true);
        assertTrue(card.isChecked());
        card.setChecked(false);
        assertFalse(card.isChecked());
    }
}
