// SPDX-License-Identifier: GPL-3.0-or-later
package io.github.muntashirakon.AppManager.main;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Environment;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import com.google.android.material.card.MaterialCardView;
import com.google.android.material.chip.Chip;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

import io.github.muntashirakon.AppManager.R;
import io.github.muntashirakon.AppManager.utils.appearance.AppearanceUtils;
import io.github.muntashirakon.view.AutoFitGridLayoutManager;

/**
 * AMUI-04B: bounded, read-only viewport/recycling stress on API35/API36.
 * All app rows are synthetic. Never installs, removes, filters, or modifies real packages.
 * View recreation is tested; process death, actual Activity recreation and work profiles are NOT.
 */
@RunWith(AndroidJUnit4.class)
public class Amui04BViewportStressInstrumentedTest {
    private static final int LARGE_LIST_SIZE = 600;

    private Context themedContext() {
        return AppearanceUtils.getThemedContext(
                InstrumentationRegistry.getInstrumentation().getTargetContext(), false);
    }

    private static final class SyntheticHolder extends RecyclerView.ViewHolder {
        final MaterialCardView card;
        final TextView label;
        final TextView packageName;
        SyntheticHolder(@NonNull View view) {
            super(view);
            card = (MaterialCardView) view;
            label = view.findViewById(R.id.label);
            packageName = view.findViewById(R.id.packageName);
        }
    }

    private static final class SyntheticAdapter extends RecyclerView.Adapter<SyntheticHolder> {
        private final int count;
        SyntheticAdapter(int count) {
            this.count = count;
            setHasStableIds(true);
        }
        @NonNull @Override
        public SyntheticHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new SyntheticHolder(LayoutInflater.from(parent.getContext())
                    .inflate(R.layout.item_main, parent, false));
        }
        @Override
        public void onBindViewHolder(@NonNull SyntheticHolder holder, int position) {
            holder.label.setText("Synthetic app #" + position);
            holder.packageName.setText("org.example.visual.long.synthetic.package." + position);
            // Explicitly reset every recycled card; no real package/selection mutation.
            holder.card.setChecked((position % 2) == 0);
        }
        @Override public long getItemId(int position) { return 200000L + position; }
        @Override public int getItemCount() { return count; }
    }

    private RecyclerView recycler(Context context, int count, int columnPx) {
        RecyclerView list = new RecyclerView(context);
        list.setLayoutManager(new AutoFitGridLayoutManager(context, columnPx));
        list.setAdapter(new SyntheticAdapter(count));
        return list;
    }

    private void size(View view, int width, int height) {
        view.measure(View.MeasureSpec.makeMeasureSpec(width, View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(height, View.MeasureSpec.EXACTLY));
        view.layout(0, 0, width, height);
    }

    @Test
    public void largeSyntheticListOnlyBindsVisibleRows() {
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            RecyclerView list = recycler(themedContext(), LARGE_LIST_SIZE, 640);
            size(list, 720, 1080);
            assertEquals(LARGE_LIST_SIZE, list.getAdapter().getItemCount());
            assertTrue("Expected visible list rows", list.getChildCount() > 0);
            assertTrue("Virtualization lost", list.getChildCount() < 100);
            assertEquals(200599L, list.getAdapter().getItemId(599));
        });
    }

    @Test
    public void resizingNarrowWideAndBackRecomputesRealLayoutSpans() {
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            RecyclerView list = recycler(themedContext(), LARGE_LIST_SIZE, 640);
            AutoFitGridLayoutManager manager = (AutoFitGridLayoutManager) list.getLayoutManager();
            for (int width : new int[] {720, 1920, 1080, 720}) {
                size(list, width, 1000);
                assertEquals("Grid span did not follow width", Math.max(1, width / 640), manager.getSpanCount());
                assertTrue("Rows vanished after width change", list.getChildCount() > 0);
            }
        });
    }

    @Test
    public void repeatedScrollAndRecycleKeepSyntheticStableIds() {
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            RecyclerView list = recycler(themedContext(), LARGE_LIST_SIZE, 640);
            SyntheticAdapter adapter = (SyntheticAdapter) list.getAdapter();
            for (int position : new int[] {0, 350, 599, 70, 500, 0}) {
                list.scrollToPosition(position);
                size(list, 960, 1100);
                assertTrue("Recycling lost visible rows", list.getChildCount() > 0);
                assertEquals(200000L + position, adapter.getItemId(position));
                for (int n = 0; n < list.getChildCount(); n++) {
                    View row = list.getChildAt(n);
                    int bound = list.getChildAdapterPosition(row);
                    if (bound != RecyclerView.NO_POSITION) {
                        assertEquals("Recycled checked state was stale", (bound % 2) == 0,
                                ((MaterialCardView) row).isChecked());
                    }
                }
            }
        });
    }

    @Test
    public void quickChipsRemainInteractiveAfterWidthAndRtlChanges() {
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            Context context = themedContext();
            for (int width : new int[] {360, 720, 1920}) {
                View filters = LayoutInflater.from(context)
                        .inflate(R.layout.amui03c_quick_filters, null, false);
                filters.setLayoutDirection(width == 360 ? View.LAYOUT_DIRECTION_RTL
                        : View.LAYOUT_DIRECTION_LTR);
                size(filters, width, 100);
                Chip user = filters.findViewById(R.id.amui03c_user);
                Chip advanced = filters.findViewById(R.id.amui03c_advanced);
                assertNotNull(user);
                assertNotNull(advanced);
                assertTrue(user.isCheckable());
                user.setChecked(true);
                assertTrue(user.isChecked());
                user.setChecked(false);
                assertTrue(!user.isChecked());
                assertTrue(!advanced.isCheckable());
            }
        });
    }

    @Test
    public void repeatedViewRecreationPreservesAllAdapterBindingIds() {
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            Context context = themedContext();
            int[] required = {R.id.icon, R.id.backup_indicator, R.id.favorite_icon,
                    R.id.label, R.id.packageName, R.id.version, R.id.isSystem,
                    R.id.size, R.id.date, R.id.shareid, R.id.issuer, R.id.sha,
                    R.id.backup_info, R.id.backup_info_ext};
            for (int iteration = 0; iteration < 20; iteration++) {
                View row = LayoutInflater.from(context).inflate(R.layout.item_main, null, false);
                row.setLayoutDirection((iteration % 2) == 0 ? View.LAYOUT_DIRECTION_LTR
                        : View.LAYOUT_DIRECTION_RTL);
                size(row, 720 + (iteration % 3) * 240, 240);
                for (int id : required) assertNotNull("Missing binding ID " + id, row.findViewById(id));
                MaterialCardView card = (MaterialCardView) row;
                card.setChecked(true);
                assertTrue(card.isChecked());
                card.setChecked(false);
                assertTrue(!card.isChecked());
            }
        });
    }

    private Bitmap viewportBitmap(int width, int height, boolean rtl) {
        final Bitmap[] result = new Bitmap[1];
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
            Context context = themedContext();
            LinearLayout root = new LinearLayout(context);
            root.setOrientation(LinearLayout.VERTICAL);
            root.setBackgroundColor(android.graphics.Color.rgb(247, 247, 247));
            root.setLayoutDirection(rtl ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
            View filters = LayoutInflater.from(context).inflate(R.layout.amui03c_quick_filters, root, false);
            root.addView(filters, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            TextView sceneLabel = new TextView(context);
            sceneLabel.setText(rtl ? "RTL viewport fixture"
                    : (width >= 1500 ? "Wide viewport fixture" : "Narrow viewport fixture"));
            sceneLabel.setPadding(24, 12, 24, 12);
            root.addView(sceneLabel, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            RecyclerView list = recycler(context, LARGE_LIST_SIZE, 640);
            root.addView(list, new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
            // The captured pixels are an app-list UI fixture, NOT a real MainActivity screen.
            size(root, width, height);
            assertTrue("No list children in render fixture", list.getChildCount() > 0);
            Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
            root.draw(new Canvas(bitmap));
            result[0] = bitmap;
        });
        assertNotNull(result[0]);
        return result[0];
    }

    private void snapshot(String name, int width, int height, boolean rtl) throws IOException {
        Context target = InstrumentationRegistry.getInstrumentation().getTargetContext();
        File pictures = target.getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        assertNotNull("App-scoped screenshot directory unavailable", pictures);
        File dir = new File(pictures, "amui04b");
        assertTrue("Could not create app-scoped screenshots", dir.isDirectory() || dir.mkdirs());
        File out = new File(dir, name + ".png");
        Bitmap bitmap = viewportBitmap(width, height, rtl);
        try (FileOutputStream writer = new FileOutputStream(out)) {
            assertTrue("PNG encoding failed", bitmap.compress(Bitmap.CompressFormat.PNG, 100, writer));
            writer.flush();
        } finally {
            bitmap.recycle();
        }
        assertTrue("Screenshot missing/empty", out.isFile() && out.length() > 2048);
    }

    @Test
    public void captureNarrowWideAndRtlViewportEvidence() throws IOException {
        snapshot("narrow", 720, 1280, false);
        snapshot("wide", 1920, 1200, false);
        snapshot("rtl", 720, 1280, true);
    }
}
