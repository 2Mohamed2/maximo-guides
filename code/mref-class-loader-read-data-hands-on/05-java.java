private static Filter filter(String field, String value) {
    Filter f = new Filter();
    f.setSectionName("General");
    f.setFieldName(field);
    f.setDataType(STRING);
    f.setOperator(EQUALS);
    f.setValue(value);
    return f;
}
