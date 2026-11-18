/** Who MREF says is calling: the request attributes MREF sets before execute(). */
private String me(HttpServletRequest req) {
    return "{\"userId\":" + req.getAttribute(ATTR_UID) + ",\"userName\":" + q(String.valueOf(req.getAttribute(ATTR_UNAME)))
        + ",\"language\":" + q(String.valueOf(req.getAttribute(ATTR_LANGUAGE))) + "}";
}
