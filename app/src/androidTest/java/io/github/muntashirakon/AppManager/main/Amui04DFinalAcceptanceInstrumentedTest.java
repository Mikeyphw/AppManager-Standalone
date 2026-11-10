// SPDX-License-Identifier: GPL-3.0-or-later
package io.github.muntashirakon.AppManager.main;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import android.app.Application;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.graphics.Color;
import android.net.Uri;
import android.os.Process;
import android.view.LayoutInflater;
import android.view.View;

import androidx.lifecycle.MutableLiveData;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import com.google.android.material.chip.Chip;
import com.google.android.material.color.MaterialColors;

import org.junit.After;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;

import io.github.muntashirakon.AppManager.R;
import io.github.muntashirakon.AppManager.types.PackageChangeReceiver;
import io.github.muntashirakon.AppManager.utils.appearance.AppearanceUtils;

/**
 * AMUI-04D: final hosted-device read-only acceptance. The existing AMUI-01
 * disposable fixture owns real install/remove mutation; this class MUST NOT.
 * Process death, wallpaper mutation, work-profile creation and physical arm64
 * are NOT implied by these tests.
 */
@RunWith(AndroidJUnit4.class)
public class Amui04DFinalAcceptanceInstrumentedTest {
    private MainViewModel model;

    private Context target() {
        return InstrumentationRegistry.getInstrumentation().getTargetContext();
    }

    private MainViewModel createModel() {
        model = new MainViewModel((Application) target().getApplicationContext());
        return model;
    }

    @After
    public void disposeOwnedViewModel() {
        if (model != null) {
            InstrumentationRegistry.getInstrumentation().waitForIdleSync();
            model.onCleared();
            model = null;
        }
    }

    @Test
    public void installedDebugPackageHasRealUidAndMetadata() throws Exception {
        Context context = target();
        PackageInfo info = context.getPackageManager().getPackageInfo(context.getPackageName(), 0);
        assertNotNull(info);
        assertNotNull(info.applicationInfo);
        assertEquals(context.getApplicationInfo().uid, info.applicationInfo.uid);
        assertEquals(Process.myUid(), info.applicationInfo.uid);
        assertTrue(context.getPackageName().endsWith(".debug"));
    }

    @Test
    public void packageAddedIntentUsesExactPackageUriNotSharedUid() {
        Intent intent = new Intent(Intent.ACTION_PACKAGE_ADDED,
                Uri.parse("package:io.github.muntashirakon.amui04d.fixture"));
        intent.putExtra(Intent.EXTRA_UID, 12345);
        assertArrayEquals(new String[]{"io.github.muntashirakon.amui04d.fixture"},
                PackageChangeReceiver.packagesFromPackageIntent(intent));
    }

    @Test
    public void packageArrayPreservesExactTwoTargets() {
        Intent intent = new Intent(Intent.ACTION_EXTERNAL_APPLICATIONS_UNAVAILABLE);
        intent.putExtra(Intent.EXTRA_CHANGED_PACKAGE_LIST, new String[]{"synthetic.one", "synthetic.two"});
        assertArrayEquals(new String[]{"synthetic.one", "synthetic.two"},
                PackageChangeReceiver.packagesFromPackageIntent(intent));
    }

    @Test
    public void missingPackageUriDoesNotInventPackage() {
        Intent intent = new Intent(Intent.ACTION_PACKAGE_ADDED);
        intent.putExtra(Intent.EXTRA_UID, 12345);
        assertNull(PackageChangeReceiver.packagesFromPackageIntent(intent));
    }

    @Test
    public void packageRemovedReplacingIsNotMistakenForDeletionReceipt() {
        Intent intent = new Intent(Intent.ACTION_PACKAGE_REMOVED,
                Uri.parse("package:synthetic.replace"));
        intent.putExtra(Intent.EXTRA_REPLACING, true);
        // Exact URI parsing does not perform a deletion; dispatcher owns replacing semantics.
        assertArrayEquals(new String[]{"synthetic.replace"},
                PackageChangeReceiver.packagesFromPackageIntent(intent));
    }

    @Test
    public void appListStatusKeepsInaccessibleProfilesAsPartial() {
        AppListSyncStatus original = AppListSyncStatus.success("resume", 60, 2, 1, 9);
        AppListSyncStatus visible = original.withVisibleCount(16, true);
        assertTrue(visible.success);
        assertTrue(visible.partial);
        assertTrue(visible.filtered);
        assertEquals(60, visible.sourceCount);
        assertEquals(16, visible.visibleCount);
        assertEquals(1, visible.skippedUsers);
        assertEquals(0, original.visibleCount);
    }

    @Test
    public void failureStatusCannotBecomeSuccessfulResult() {
        AppListSyncStatus failure = AppListSyncStatus.failure("package-event-failure", "SecurityException");
        assertFalse(failure.running);
        assertFalse(failure.success);
        assertFalse(failure.partial);
        assertEquals("SecurityException", failure.error);
        assertEquals("package-event-failure", failure.reason);
    }

    @SuppressWarnings("unchecked")
    @Test
    public void publishedApplicationSnapshotIsUnmodifiable() throws Exception {
        MainViewModel vm = createModel();
        Field epoch = MainViewModel.class.getDeclaredField("mListEpoch");
        epoch.setAccessible(true);
        long generation = ((AtomicLong) epoch.get(vm)).get();
        Method publish = MainViewModel.class.getDeclaredMethod("publishVisibleItems", List.class, long.class);
        publish.setAccessible(true);
        publish.invoke(vm, Collections.<ApplicationItem>emptyList(), generation);
        InstrumentationRegistry.getInstrumentation().waitForIdleSync();
        List<ApplicationItem> snapshot = vm.getApplicationItems().getValue();
        assertNotNull(snapshot);
        try {
            snapshot.add(null);
            fail("Published list must be immutable");
        } catch (UnsupportedOperationException expected) {
            assertEquals(0, snapshot.size());
        }
    }

    @Test
    public void firstResumeRemainsNonScanningAndNonSuccessful() {
        MainViewModel vm = createModel();
        vm.onResume();
        InstrumentationRegistry.getInstrumentation().waitForIdleSync();
        assertNull("First resume should not invent a successful scan", vm.getRefreshState().getValue());
    }

    @Test
    public void semanticColorsAndQuickFiltersInflateWithActualTheme() {
        Context themed = AppearanceUtils.getThemedContext(target(), false);
        int primary = MaterialColors.getColor(themed, androidx.appcompat.R.attr.colorPrimary,
                "AMUI04D_PRIMARY");
        int surface = MaterialColors.getColor(themed, com.google.android.material.R.attr.colorSurface,
                "AMUI04D_SURFACE");
        assertNotEquals(Color.TRANSPARENT, primary);
        assertNotEquals(Color.TRANSPARENT, surface);
        View quick = LayoutInflater.from(themed).inflate(R.layout.amui03c_quick_filters, null, false);
        Chip user = quick.findViewById(R.id.amui03c_user);
        assertNotNull(user);
        assertTrue(user.isCheckable());
        assertNotNull(quick.findViewById(R.id.amui03c_summary));
    }
}
