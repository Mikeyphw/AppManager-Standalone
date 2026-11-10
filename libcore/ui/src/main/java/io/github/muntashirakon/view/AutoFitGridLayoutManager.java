// SPDX-License-Identifier: GPL-3.0-or-later

package io.github.muntashirakon.view;

import android.content.Context;

import androidx.annotation.Px;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

// Source: https://stackoverflow.com/a/55487382
// Copyright 2019 Vishal Nagvadiya
public class AutoFitGridLayoutManager extends GridLayoutManager {
    @Px
    private int mColumnWidth;
    private boolean mColumnWidthChanged = true;
    private int mLastAvailableSpace = -1;

    public AutoFitGridLayoutManager(Context context, @Px int columnWidth) {
        super(context, 1);
        setColumnWidth(columnWidth);
    }


    public void setColumnWidth(@Px int newColumnWidth) {
        if (newColumnWidth > 0 && newColumnWidth != mColumnWidth) {
            mColumnWidth = newColumnWidth;
            mColumnWidthChanged = true;
        }
    }

    /** Pure size calculation; available width already excludes RecyclerView padding. */
    public static int calculateSpanCount(int availableSpace, int columnWidth) {
        if (columnWidth <= 0) return 1;
        return Math.max(1, Math.max(0, availableSpace) / columnWidth);
    }

    @Override
    public void onLayoutChildren(RecyclerView.Recycler recycler, RecyclerView.State state) {
        // Folded-window resizing can change width without calling setColumnWidth.
        int availableSpace = getOrientation() == VERTICAL
                ? getWidth() - getPaddingRight() - getPaddingLeft()
                : getHeight() - getPaddingTop() - getPaddingBottom();
        if ((mColumnWidthChanged || availableSpace != mLastAvailableSpace) && mColumnWidth > 0) {
            int spanCount = calculateSpanCount(availableSpace, mColumnWidth);
            if (getSpanCount() != spanCount) setSpanCount(spanCount);
            mLastAvailableSpace = availableSpace;
            mColumnWidthChanged = false;
        }
        super.onLayoutChildren(recycler, state);
    }
}
