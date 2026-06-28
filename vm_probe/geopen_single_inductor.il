procedure(CDX_geOpenSingleInductor()
  let((win)
    win = geOpen(?lib "codex_fdl_bridge" ?cell "single_inductor_12s_3p5t_test" ?view "layout")
    printf("CDX_GEOPEN_WINDOW=%L\n" win)
    when(win hiZoomFit(win))
  )
)

hiEnqueueCmd("CDX_geOpenSingleInductor()")
