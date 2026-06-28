procedure(CDX_queryLayerNumbers()
  let((tf layers)
    tf = techGetTechFile(ddGetObj("codex_fdl_bridge"))
    layers = list("M1" "M2" "M3" "M4" "M5" "M6" "V1" "V2" "V3" "V4" "V5" "M4TXT" "M5TXT")
    foreach(layer layers
      printf("%s layerNum=%L purposeNum=%L lpp=%L\n"
        layer
        techGetLayerNum(tf layer)
        techGetPurposeNum(tf "drawing")
        techGetLP(tf list(layer "drawing"))
      )
    )
  )
)

CDX_queryLayerNumbers()
exit()
