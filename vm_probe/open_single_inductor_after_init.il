procedure(CDX_openSingleInductor()
  let((win)
    win = deOpenCellView("codex_fdl_bridge" "single_inductor_12s_3p5t_test" "layout" "maskLayout" nil "r")
    printf("CDX_OPEN_WINDOW=%L\n" win)
    when(win
      hiZoomFit(win)
    )
  )
)

hiEnqueueCmd("CDX_openSingleInductor()")
