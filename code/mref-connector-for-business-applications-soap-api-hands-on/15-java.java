import com.tririga.pub.workflow.CustomBusinessConnectTask;
import com.tririga.pub.workflow.Record;
import com.tririga.ws.TririgaWS;
import com.tririga.ws.dto.IntegrationField;
import com.tririga.ws.dto.IntegrationRecord;
import com.tririga.ws.dto.IntegrationSection;
import com.tririga.ws.dto.ResponseHelperHeader;

public class CreateFollowUpTask implements CustomBusinessConnectTask {
    @Override
    public boolean execute(TririgaWS tws, long userId, Record[] records) {
        try {
            long typeId = tws.getObjectTypeId("triTask", "triWorkTask");
            IntegrationRecord r = new IntegrationRecord();
            r.setModuleId(tws.getModuleId("triTask"));
            r.setObjectTypeId(typeId);
            r.setObjectTypeName("triWorkTask");
            r.setGuiId(tws.getDefaultGuiId(typeId));
            r.setId(-1);
            r.setActionName("triCreateDraft");
            IntegrationSection s = new IntegrationSection("RecordInformation");
            s.setFields(new IntegrationField[]{
                new IntegrationField("triNameTX", "Follow-up inspection"),
                new IntegrationField("triTaskTypeCL", "Corrective"),
                new IntegrationField("triCurrencyUO", "US Dollars")});
            r.setSections(new IntegrationSection[]{s});
            ResponseHelperHeader h = tws.saveRecord(new IntegrationRecord[]{r});
            return !h.isAnyFailed();
        } catch (Exception e) {
            return false;
        }
    }
}
