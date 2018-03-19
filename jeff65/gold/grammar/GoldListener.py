# Generated from jeff65/gold/grammar/Gold.g4 by ANTLR 4.5.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .Gold import Gold
else:
    from Gold import Gold

# This class defines a complete listener for a parse tree produced by Gold.
class GoldListener(ParseTreeListener):

    # Enter a parse tree produced by Gold#ExprParen.
    def enterExprParen(self, ctx:Gold.ExprParenContext):
        pass

    # Exit a parse tree produced by Gold#ExprParen.
    def exitExprParen(self, ctx:Gold.ExprParenContext):
        pass


    # Enter a parse tree produced by Gold#ExprBitXor.
    def enterExprBitXor(self, ctx:Gold.ExprBitXorContext):
        pass

    # Exit a parse tree produced by Gold#ExprBitXor.
    def exitExprBitXor(self, ctx:Gold.ExprBitXorContext):
        pass


    # Enter a parse tree produced by Gold#ExprSum.
    def enterExprSum(self, ctx:Gold.ExprSumContext):
        pass

    # Exit a parse tree produced by Gold#ExprSum.
    def exitExprSum(self, ctx:Gold.ExprSumContext):
        pass


    # Enter a parse tree produced by Gold#ExprIndex.
    def enterExprIndex(self, ctx:Gold.ExprIndexContext):
        pass

    # Exit a parse tree produced by Gold#ExprIndex.
    def exitExprIndex(self, ctx:Gold.ExprIndexContext):
        pass


    # Enter a parse tree produced by Gold#ExprBitShift.
    def enterExprBitShift(self, ctx:Gold.ExprBitShiftContext):
        pass

    # Exit a parse tree produced by Gold#ExprBitShift.
    def exitExprBitShift(self, ctx:Gold.ExprBitShiftContext):
        pass


    # Enter a parse tree produced by Gold#ExprNegation.
    def enterExprNegation(self, ctx:Gold.ExprNegationContext):
        pass

    # Exit a parse tree produced by Gold#ExprNegation.
    def exitExprNegation(self, ctx:Gold.ExprNegationContext):
        pass


    # Enter a parse tree produced by Gold#ExprBitOr.
    def enterExprBitOr(self, ctx:Gold.ExprBitOrContext):
        pass

    # Exit a parse tree produced by Gold#ExprBitOr.
    def exitExprBitOr(self, ctx:Gold.ExprBitOrContext):
        pass


    # Enter a parse tree produced by Gold#ExprDeref.
    def enterExprDeref(self, ctx:Gold.ExprDerefContext):
        pass

    # Exit a parse tree produced by Gold#ExprDeref.
    def exitExprDeref(self, ctx:Gold.ExprDerefContext):
        pass


    # Enter a parse tree produced by Gold#ExprProduct.
    def enterExprProduct(self, ctx:Gold.ExprProductContext):
        pass

    # Exit a parse tree produced by Gold#ExprProduct.
    def exitExprProduct(self, ctx:Gold.ExprProductContext):
        pass


    # Enter a parse tree produced by Gold#ExprCompare.
    def enterExprCompare(self, ctx:Gold.ExprCompareContext):
        pass

    # Exit a parse tree produced by Gold#ExprCompare.
    def exitExprCompare(self, ctx:Gold.ExprCompareContext):
        pass


    # Enter a parse tree produced by Gold#ExprFunCall.
    def enterExprFunCall(self, ctx:Gold.ExprFunCallContext):
        pass

    # Exit a parse tree produced by Gold#ExprFunCall.
    def exitExprFunCall(self, ctx:Gold.ExprFunCallContext):
        pass


    # Enter a parse tree produced by Gold#ExprNumber.
    def enterExprNumber(self, ctx:Gold.ExprNumberContext):
        pass

    # Exit a parse tree produced by Gold#ExprNumber.
    def exitExprNumber(self, ctx:Gold.ExprNumberContext):
        pass


    # Enter a parse tree produced by Gold#ExprBitAnd.
    def enterExprBitAnd(self, ctx:Gold.ExprBitAndContext):
        pass

    # Exit a parse tree produced by Gold#ExprBitAnd.
    def exitExprBitAnd(self, ctx:Gold.ExprBitAndContext):
        pass


    # Enter a parse tree produced by Gold#ExprBitNot.
    def enterExprBitNot(self, ctx:Gold.ExprBitNotContext):
        pass

    # Exit a parse tree produced by Gold#ExprBitNot.
    def exitExprBitNot(self, ctx:Gold.ExprBitNotContext):
        pass


    # Enter a parse tree produced by Gold#ExprId.
    def enterExprId(self, ctx:Gold.ExprIdContext):
        pass

    # Exit a parse tree produced by Gold#ExprId.
    def exitExprId(self, ctx:Gold.ExprIdContext):
        pass


    # Enter a parse tree produced by Gold#ExprMember.
    def enterExprMember(self, ctx:Gold.ExprMemberContext):
        pass

    # Exit a parse tree produced by Gold#ExprMember.
    def exitExprMember(self, ctx:Gold.ExprMemberContext):
        pass


    # Enter a parse tree produced by Gold#array.
    def enterArray(self, ctx:Gold.ArrayContext):
        pass

    # Exit a parse tree produced by Gold#array.
    def exitArray(self, ctx:Gold.ArrayContext):
        pass


    # Enter a parse tree produced by Gold#storage.
    def enterStorage(self, ctx:Gold.StorageContext):
        pass

    # Exit a parse tree produced by Gold#storage.
    def exitStorage(self, ctx:Gold.StorageContext):
        pass


    # Enter a parse tree produced by Gold#TypePrimitive.
    def enterTypePrimitive(self, ctx:Gold.TypePrimitiveContext):
        pass

    # Exit a parse tree produced by Gold#TypePrimitive.
    def exitTypePrimitive(self, ctx:Gold.TypePrimitiveContext):
        pass


    # Enter a parse tree produced by Gold#TypeSlice.
    def enterTypeSlice(self, ctx:Gold.TypeSliceContext):
        pass

    # Exit a parse tree produced by Gold#TypeSlice.
    def exitTypeSlice(self, ctx:Gold.TypeSliceContext):
        pass


    # Enter a parse tree produced by Gold#TypePointer.
    def enterTypePointer(self, ctx:Gold.TypePointerContext):
        pass

    # Exit a parse tree produced by Gold#TypePointer.
    def exitTypePointer(self, ctx:Gold.TypePointerContext):
        pass


    # Enter a parse tree produced by Gold#TypeArray.
    def enterTypeArray(self, ctx:Gold.TypeArrayContext):
        pass

    # Exit a parse tree produced by Gold#TypeArray.
    def exitTypeArray(self, ctx:Gold.TypeArrayContext):
        pass


    # Enter a parse tree produced by Gold#rangeTo.
    def enterRangeTo(self, ctx:Gold.RangeToContext):
        pass

    # Exit a parse tree produced by Gold#rangeTo.
    def exitRangeTo(self, ctx:Gold.RangeToContext):
        pass


    # Enter a parse tree produced by Gold#declaration.
    def enterDeclaration(self, ctx:Gold.DeclarationContext):
        pass

    # Exit a parse tree produced by Gold#declaration.
    def exitDeclaration(self, ctx:Gold.DeclarationContext):
        pass


    # Enter a parse tree produced by Gold#stmtConstant.
    def enterStmtConstant(self, ctx:Gold.StmtConstantContext):
        pass

    # Exit a parse tree produced by Gold#stmtConstant.
    def exitStmtConstant(self, ctx:Gold.StmtConstantContext):
        pass


    # Enter a parse tree produced by Gold#stmtUse.
    def enterStmtUse(self, ctx:Gold.StmtUseContext):
        pass

    # Exit a parse tree produced by Gold#stmtUse.
    def exitStmtUse(self, ctx:Gold.StmtUseContext):
        pass


    # Enter a parse tree produced by Gold#stmtLet.
    def enterStmtLet(self, ctx:Gold.StmtLetContext):
        pass

    # Exit a parse tree produced by Gold#stmtLet.
    def exitStmtLet(self, ctx:Gold.StmtLetContext):
        pass


    # Enter a parse tree produced by Gold#stmtWhile.
    def enterStmtWhile(self, ctx:Gold.StmtWhileContext):
        pass

    # Exit a parse tree produced by Gold#stmtWhile.
    def exitStmtWhile(self, ctx:Gold.StmtWhileContext):
        pass


    # Enter a parse tree produced by Gold#stmtFor.
    def enterStmtFor(self, ctx:Gold.StmtForContext):
        pass

    # Exit a parse tree produced by Gold#stmtFor.
    def exitStmtFor(self, ctx:Gold.StmtForContext):
        pass


    # Enter a parse tree produced by Gold#stmtIf.
    def enterStmtIf(self, ctx:Gold.StmtIfContext):
        pass

    # Exit a parse tree produced by Gold#stmtIf.
    def exitStmtIf(self, ctx:Gold.StmtIfContext):
        pass


    # Enter a parse tree produced by Gold#stmtIsr.
    def enterStmtIsr(self, ctx:Gold.StmtIsrContext):
        pass

    # Exit a parse tree produced by Gold#stmtIsr.
    def exitStmtIsr(self, ctx:Gold.StmtIsrContext):
        pass


    # Enter a parse tree produced by Gold#stmtFun.
    def enterStmtFun(self, ctx:Gold.StmtFunContext):
        pass

    # Exit a parse tree produced by Gold#stmtFun.
    def exitStmtFun(self, ctx:Gold.StmtFunContext):
        pass


    # Enter a parse tree produced by Gold#stmtReturn.
    def enterStmtReturn(self, ctx:Gold.StmtReturnContext):
        pass

    # Exit a parse tree produced by Gold#stmtReturn.
    def exitStmtReturn(self, ctx:Gold.StmtReturnContext):
        pass


    # Enter a parse tree produced by Gold#stmtAssignVal.
    def enterStmtAssignVal(self, ctx:Gold.StmtAssignValContext):
        pass

    # Exit a parse tree produced by Gold#stmtAssignVal.
    def exitStmtAssignVal(self, ctx:Gold.StmtAssignValContext):
        pass


    # Enter a parse tree produced by Gold#stmtAssignInc.
    def enterStmtAssignInc(self, ctx:Gold.StmtAssignIncContext):
        pass

    # Exit a parse tree produced by Gold#stmtAssignInc.
    def exitStmtAssignInc(self, ctx:Gold.StmtAssignIncContext):
        pass


    # Enter a parse tree produced by Gold#stmtAssignDec.
    def enterStmtAssignDec(self, ctx:Gold.StmtAssignDecContext):
        pass

    # Exit a parse tree produced by Gold#stmtAssignDec.
    def exitStmtAssignDec(self, ctx:Gold.StmtAssignDecContext):
        pass


    # Enter a parse tree produced by Gold#block.
    def enterBlock(self, ctx:Gold.BlockContext):
        pass

    # Exit a parse tree produced by Gold#block.
    def exitBlock(self, ctx:Gold.BlockContext):
        pass


    # Enter a parse tree produced by Gold#unit.
    def enterUnit(self, ctx:Gold.UnitContext):
        pass

    # Exit a parse tree produced by Gold#unit.
    def exitUnit(self, ctx:Gold.UnitContext):
        pass


