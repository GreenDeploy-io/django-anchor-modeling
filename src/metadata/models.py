# class DataChange(AnchorNoBusinessId, CreatedModel):
#     pass


# StaticAttributeForDataChangeReason = static_attribute(
#     anchor_class=DataChange,
#     value_type=models.TextField(),
#     related_name="reason",
# )


# class DataChangeReason(StaticAttributeForDataChangeReason):
#     pass


# class RequestCall(AnchorNoBusinessId):
#     pass


# StaticAttributeForRequestCallArgs = static_attribute(
#     anchor_class=RequestCall,
#     value_type=models.JSONField(default=dict),
#     related_name="request_args",
# )


# class RequestCallArgs(StaticAttributeForRequestCallArgs):
#     pass


# StaticAttributeForRequestUser = static_attribute(
#     anchor_class=RequestCall,
#     value_type=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
#     related_name="request_user",
# )


# class RequestUser(StaticAttributeForRequestUser):
#     pass


# class RequestUrl(Knot):
#     pass


# StaticAttributeForRequestCallUrl = static_attribute(
#     anchor_class=RequestCall,
#     value_type=models.ForeignKey(RequestUrl, on_delete=models.CASCADE),
#     related_name="request_url",
# )


# class RequestCallUrl(StaticAttributeForRequestCallUrl):
#     pass


# class FunctionCall(AnchorNoBusinessId):
#     pass


# StaticAttributeForFunctionCallArgs = static_attribute(
#     anchor_class=FunctionCall,
#     value_type=models.JSONField(default=dict),
#     related_name="function_args",
# )


# class FunctionCallArgs(StaticAttributeForFunctionCallArgs):
#     pass


# class ServiceFunction(Knot):
#     pass


# StaticAttributeForFunctionCallSvcFunc = static_attribute(
#     anchor_class=FunctionCall,
#     value_type=models.ForeignKey(ServiceFunction, on_delete=models.CASCADE),
#     related_name="function_signature",
# )


# class FunctionCallServiceFunction(StaticAttributeForFunctionCallSvcFunc):
#     pass
