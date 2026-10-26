import { TurbineSearchPage } from '../pages/TurbineSearchPage';
import { StockSelectionPage } from '../pages/StockSelectionPage';

export async function navigateToStep3WithSelectedValves(
  searchPage: TurbineSearchPage,
  stockSelectionPage: StockSelectionPage
): Promise<void> {
  await searchPage.open();
  await searchPage.filterByModel('Т-110');
  await searchPage.selectTurbineByName('Т-110/120-130');

  await stockSelectionPage.setValveQuantity('Клапан РК-1', 2);
  await stockSelectionPage.setValveQuantity('Клапан СК-1', 1);
  await stockSelectionPage.clickNext();
}