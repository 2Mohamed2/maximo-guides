@Override
public void execute(TririgaWS tws, HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
    res.setContentType("application/json; charset=UTF-8");
    res.setHeader("Cache-Control", "no-store");
    long t0 = System.currentTimeMillis();
    String action = req.getParameter("action") == null ? "me" : req.getParameter("action");
    String body;
    try {
        switch (action) {
            case "me" -> body = me(req);
            case "buildings" -> body = buildings(tws);
            case "floors" -> body = floors(tws, text(req.getParameter("building")));
            case "spaces" -> body = spaces(tws, text(req.getParameter("building")), text(req.getParameter("floor")));
            default -> { res.setStatus(400); body = "{\"error\":\"unknown action\"}"; }
        }
    } catch (IllegalArgumentException e) {
        res.setStatus(400);
        body = "{\"error\":" + q(e.getMessage()) + "}";
    } catch (Exception e) {
        res.setStatus(500);
        body = "{\"error\":" + q(e.getClass().getSimpleName() + ": " + e.getMessage()) + "}";
    }
    long ms = System.currentTimeMillis() - t0;
    res.getWriter().write(body.substring(0, body.length() - 1) + (body.length() > 2 ? "," : "") + "\"ms\":" + ms + "}");
}
