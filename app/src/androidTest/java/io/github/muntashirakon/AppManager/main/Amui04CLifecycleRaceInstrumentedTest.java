// SPDX-License-Identifier: GPL-3.0-or-later
package io.github.muntashirakon.AppManager.main;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import android.app.Application;
import android.content.Context;

import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.Observer;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;

import org.junit.After;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/** AMUI04C: real ViewModel publication/lifecycle state; no APK, profile or data mutation. */
@RunWith(AndroidJUnit4.class)
public class Amui04CLifecycleRaceInstrumentedTest {
    private MainViewModel model;

    private MainViewModel newModel() {
        Context ctx = InstrumentationRegistry.getInstrumentation().getTargetContext();
        model = new MainViewModel((Application) ctx.getApplicationContext());
        return model;
    }

    private static Object field(MainViewModel vm, String name) throws Exception {
        Field f = MainViewModel.class.getDeclaredField(name);
        f.setAccessible(true);
        return f.get(vm);
    }

    @SuppressWarnings("unchecked")
    private MutableLiveData<List<ApplicationItem>> items(MainViewModel vm) throws Exception {
        return (MutableLiveData<List<ApplicationItem>>) field(vm, "mApplicationItemsLiveData");
    }

    private AtomicLong epoch(MainViewModel vm) throws Exception {
        return (AtomicLong) field(vm, "mListEpoch");
    }

    private AtomicLong refresh(MainViewModel vm) throws Exception {
        return (AtomicLong) field(vm, "mRefreshRequestId");
    }

    private void publish(MainViewModel vm, long fromEpoch) throws Exception {
        Method m = MainViewModel.class.getDeclaredMethod("publishVisibleItems", List.class, long.class);
        m.setAccessible(true);
        m.invoke(vm, Collections.<ApplicationItem>emptyList(), fromEpoch);
    }

    private void idle() {
        InstrumentationRegistry.getInstrumentation().waitForIdleSync();
    }

    @After
    public void dispose() {
        if (model != null) {
            idle();
            model.onCleared();
            model = null;
        }
    }

    @Test
    public void staleFilterEpochCannotPublishAfterLaterChange() throws Exception {
        MainViewModel vm = newModel();
        epoch(vm).set(43L);
        publish(vm, 42L);
        idle();
        assertNull("stale publication escaped epoch check", items(vm).getValue());
    }

    @Test
    public void currentFilterEpochPublishesImmutableEmptySnapshot() throws Exception {
        MainViewModel vm = newModel();
        epoch(vm).set(21L);
        publish(vm, 21L);
        idle();
        assertNotNull(items(vm).getValue());
        assertEquals(0, items(vm).getValue().size());
    }

    @Test
    public void thirtyTwoInvalidationsOnlyPublishTheLastGeneration() throws Exception {
        MainViewModel vm = newModel();
        MutableLiveData<List<ApplicationItem>> live = items(vm);
        AtomicInteger count = new AtomicInteger();
        Observer<List<ApplicationItem>> observer = value -> count.incrementAndGet();
        InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> live.observeForever(observer));
        try {
            for (long n = 1L; n <= 32L; n++) {
                epoch(vm).set(n + 1L);
                publish(vm, n);
            }
            publish(vm, 33L);
            idle();
            assertEquals("stale snapshots entered UI observer", 1, count.get());
        } finally {
            InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> live.removeObserver(observer));
        }
    }

    @Test
    public void supersededRefreshCompletionCannotMasqueradeAsNewer() throws Exception {
        MainViewModel vm = newModel();
        refresh(vm).set(2L);
        epoch(vm).set(7L);
        Field pending = MainViewModel.class.getDeclaredField("mPendingCompletion");
        pending.setAccessible(true);
        pending.set(vm, AppListSyncStatus.success("old", 8, 1, 0, 1));
        Field request = MainViewModel.class.getDeclaredField("mPendingCompletionRequestId");
        request.setAccessible(true);
        request.setLong(vm, 1L);
        publish(vm, 7L);
        idle();
        assertNull("old refresh completion marked new refresh successful", vm.getRefreshState().getValue());
    }

    @Test
    public void partialRefreshReceiptRemainsPartialAfterVisibleFiltering() {
        AppListSyncStatus original = AppListSyncStatus.success("resume", 30, 1, 1, 4);
        AppListSyncStatus visible = original.withVisibleCount(8, true);
        assertTrue(visible.success);
        assertTrue(visible.partial);
        assertTrue(visible.filtered);
        assertEquals(30, visible.sourceCount);
        assertEquals(8, visible.visibleCount);
        assertEquals(0, original.visibleCount);
        assertFalse(original.filtered);
    }

    @Test
    public void failureDoesNotInventSuccessOrLoseReason() {
        AppListSyncStatus failed = AppListSyncStatus.failure("package-event-failure", "SecurityException");
        assertFalse(failed.success);
        assertFalse(failed.running);
        assertFalse(failed.partial);
        assertEquals("SecurityException", failed.error);
        assertEquals("package-event-failure", failed.reason);
    }

    @Test
    public void firstResumeDoesNotPrematurelyClaimRefreshSuccess() {
        MainViewModel vm = newModel();
        vm.onResume();
        idle();
        assertNull("first resume cannot claim a completed scan", vm.getRefreshState().getValue());
    }
}
